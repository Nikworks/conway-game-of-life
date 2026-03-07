/**
 * Three.js 3D renderer for Conway's Game of Life.
 * Matches the public interface of Renderer (renderer.js) so main.js
 * can swap between them via `activeRenderer`.
 *
 * Visual design inspired by RBeaulieu/3DGameOfLife:
 *  - Born cells:      yellow  (#ffdd00) — alive this generation for the first time
 *  - Surviving cells: orange  (#ff6600) — alive in the previous generation too
 *  - Bounding box:    cyan wireframe outline of the grid extent
 *  - Point light at camera position (flashlight effect)
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const SCENE_BG        = 0x1a1a2e;
const BORN_COLOR      = 0xffdd00;  // yellow  — newly alive this generation
const SURVIVING_COLOR = 0xff6600;  // orange  — alive last generation too
const GRID_COLOR      = 0x2a2a4a;
const OUTLINE_COLOR   = 0x07abff;  // cyan bounding box (from reference)

export class Renderer3D {
  /**
   * @param {HTMLElement} container
   */
  constructor(container) {
    this._container = container;
    this._rows = 60;
    this._cols = 80;
    this._layers = null; // null = 2D mode
    this._gridHelper  = null;
    this._boundingBox = null;
    this._reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Born/surviving tracking — compared each update()
    this._prevAliveCells = new Set(); // "r,c" strings
    this._bornColor      = new THREE.Color(BORN_COLOR);
    this._survivingColor = new THREE.Color(SURVIVING_COLOR);

    // Scene
    this._scene = new THREE.Scene();
    this._scene.background = new THREE.Color(SCENE_BG);

    // Camera
    this._camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      2000,
    );
    this._camera.position.set(0, 40, 55);
    this._camera.lookAt(0, 0, 0);

    // Renderer
    this._renderer = new THREE.WebGLRenderer({ antialias: true });
    this._renderer.setPixelRatio(window.devicePixelRatio);
    this._renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(this._renderer.domElement);

    // Controls
    this._controls = new OrbitControls(this._camera, this._renderer.domElement);
    this._controls.enableDamping = true;
    this._controls.dampingFactor = 0.08;

    // Lights
    // Ambient: soft base light
    this._scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    // Directional: fixed fill light from upper-right
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(20, 40, 30);
    this._scene.add(dirLight);
    // Point light: follows the camera (flashlight effect, from reference)
    this._pointLight = new THREE.PointLight(0xffffff, 0.8, 500);
    this._scene.add(this._pointLight);

    // InstancedMesh for alive cells (pre-allocated for max capacity)
    this._capacity = this._rows * this._cols;
    this._cellMesh = this._buildInstancedMesh(this._capacity);
    this._scene.add(this._cellMesh);
    this._cellMesh.count = 0;

    // Reusable dummy object — avoids per-tick allocation
    this._dummy = new THREE.Object3D();

    // Grid helper + cyan bounding box
    this._buildGridHelper();
    this._buildBoundingBox();

    // Raycaster for pixelToCell
    this._raycaster = new THREE.Raycaster();
    this._groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

    // Resize observer
    this._resizeObserver = new ResizeObserver(() => this._onResize());
    this._resizeObserver.observe(container);

    // Animation loop
    this._animate();
  }

  // ------------------------------------------------------------------
  // Public API (matches Renderer interface)
  // ------------------------------------------------------------------

  /**
   * Update from a server state message and redraw.
   * @param {{ rows: number, cols: number, cells: [number, number][]|[number, number, number][], layers?: number }} state
   */
  update(state) {
    const { rows, cols, cells } = state;
    const layers = state.layers ?? null;
    const is3d = layers !== null;
    const sizeChanged = rows !== this._rows || cols !== this._cols || layers !== this._layers;

    this._rows = rows;
    this._cols = cols;
    this._layers = layers;

    if (sizeChanged) {
      const needed = is3d ? rows * cols * layers : rows * cols;
      if (needed > this._capacity) {
        this._capacity = needed;
        this._scene.remove(this._cellMesh);
        this._cellMesh.geometry.dispose();
        this._cellMesh = this._buildInstancedMesh(this._capacity);
        this._scene.add(this._cellMesh);
      }
      this._buildGridHelper();
      this._buildBoundingBox();
      this._prevAliveCells = new Set();
    }

    // Key cells for born/surviving tracking
    const currSet = new Set(
      is3d
        ? cells.map(([layer, r, c]) => `${layer},${r},${c}`)
        : cells.map(([r, c]) => `${r},${c}`)
    );
    const halfCols = cols / 2;
    const halfRows = rows / 2;
    let i = 0;

    for (const cell of cells) {
      if (is3d) {
        const [layer, r, c] = cell;
        this._dummy.position.set(c - halfCols + 0.5, layer + 0.5, r - halfRows + 0.5);
        const born = !this._prevAliveCells.has(`${layer},${r},${c}`);
        this._cellMesh.setColorAt(i, born ? this._bornColor : this._survivingColor);
      } else {
        const [r, c] = cell;
        this._dummy.position.set(c - halfCols + 0.5, 0.5, r - halfRows + 0.5);
        const born = !this._prevAliveCells.has(`${r},${c}`);
        this._cellMesh.setColorAt(i, born ? this._bornColor : this._survivingColor);
      }
      this._dummy.updateMatrix();
      this._cellMesh.setMatrixAt(i, this._dummy.matrix);
      i++;
    }

    this._cellMesh.count = i;
    this._cellMesh.instanceMatrix.needsUpdate = true;
    if (this._cellMesh.instanceColor) {
      this._cellMesh.instanceColor.needsUpdate = true;
    }

    this._prevAliveCells = currSet;

    // In reduced-motion mode, render a single frame here instead of rAF loop
    if (this._reducedMotion) {
      this._controls.update();
      this._renderer.render(this._scene, this._camera);
    }
  }

  /**
   * Adjust camera and grid for 2D vs 3D variant.
   * @param {boolean} is3d
   */
  setVariant(is3d) {
    if (is3d) {
      this._camera.position.set(0, 40, 40);
      this._camera.lookAt(0, 10, 0);
    } else {
      this._camera.position.set(0, 40, 55);
      this._camera.lookAt(0, 0, 0);
    }
    this._controls.target.set(0, is3d ? 10 : 0, 0);
    this._controls.update();
  }

  /** No-op — animation loop drives rendering continuously. */
  render() {}

  /** @param {boolean} value */
  setShowGridLines(value) {
    if (this._gridHelper)  this._gridHelper.visible  = value;
    if (this._boundingBox) this._boundingBox.visible = value;
  }

  /** No-op — hover highlight not applicable in 3D view-only mode. */
  setHoverCell(_cell) {}

  /**
   * Convert screen pixel coords to grid cell via raycasting onto y=0 plane.
   * @param {number} offsetX
   * @param {number} offsetY
   * @returns {{ row: number, col: number } | null}
   */
  pixelToCell(offsetX, offsetY) {
    const rect = this._renderer.domElement.getBoundingClientRect();
    const ndcX = (offsetX / rect.width) * 2 - 1;
    const ndcY = -(offsetY / rect.height) * 2 + 1;
    this._raycaster.setFromCamera(new THREE.Vector2(ndcX, ndcY), this._camera);
    const target = new THREE.Vector3();
    const hit = this._raycaster.ray.intersectPlane(this._groundPlane, target);
    if (!hit) return null;
    const col = Math.floor(target.x + this._cols / 2);
    const row = Math.floor(target.z + this._rows / 2);
    if (row < 0 || row >= this._rows || col < 0 || col >= this._cols) return null;
    return { row, col };
  }

  // ------------------------------------------------------------------
  // Internal helpers
  // ------------------------------------------------------------------

  _buildInstancedMesh(capacity) {
    const geo = new THREE.BoxGeometry(0.92, 1, 0.92);
    // White base so per-instance color (setColorAt) is rendered as-is
    const mat = new THREE.MeshPhongMaterial({ color: 0xffffff });
    const mesh = new THREE.InstancedMesh(geo, mat, capacity);
    // Disable frustum culling — bounding sphere is not auto-updated when
    // instance matrices change, causing Three.js to incorrectly cull the
    // entire mesh even when cells are visible.
    mesh.frustumCulled = false;
    // Pre-initialise instanceColor buffer at full capacity so setColorAt()
    // writes into a correctly-sized buffer regardless of current count.
    const defColor = new THREE.Color(SURVIVING_COLOR);
    for (let i = 0; i < capacity; i++) {
      mesh.setColorAt(i, defColor);
    }
    return mesh;
  }

  _buildGridHelper() {
    if (this._gridHelper) {
      this._scene.remove(this._gridHelper);
      this._gridHelper.geometry?.dispose();
    }
    const size = Math.max(this._rows, this._cols);
    this._gridHelper = new THREE.GridHelper(size, size, GRID_COLOR, GRID_COLOR);
    this._scene.add(this._gridHelper);
  }

  _buildBoundingBox() {
    if (this._boundingBox) {
      this._scene.remove(this._boundingBox);
      this._boundingBox.geometry?.dispose();
    }
    // Cyan wireframe outline of the cell area (cols wide × rows deep × 1 tall)
    const boxGeo   = new THREE.BoxGeometry(this._cols, 1, this._rows);
    const edgesGeo = new THREE.EdgesGeometry(boxGeo);
    boxGeo.dispose();
    const mat = new THREE.LineBasicMaterial({
      color:       OUTLINE_COLOR,
      transparent: true,
      opacity:     0.6,
    });
    this._boundingBox = new THREE.LineSegments(edgesGeo, mat);
    this._boundingBox.position.set(0, 0.5, 0); // vertically centred on cell height
    this._scene.add(this._boundingBox);
  }

  _onResize() {
    const w = this._container.clientWidth;
    const h = this._container.clientHeight;
    if (w === 0 || h === 0) return;
    this._camera.aspect = w / h;
    this._camera.updateProjectionMatrix();
    this._renderer.setSize(w, h);
  }

  _animate() {
    if (this._reducedMotion) return; // static frames only in reduced-motion mode
    requestAnimationFrame(() => this._animate());
    this._controls.update();
    // Sync point light with camera — creates a flashlight effect (from reference)
    this._pointLight.position.copy(this._camera.position);
    this._renderer.render(this._scene, this._camera);
  }
}
