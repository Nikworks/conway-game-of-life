/**
 * Three.js 3D renderer for Conway's Game of Life.
 * Matches the public interface of Renderer (renderer.js) so main.js
 * can swap between them via `activeRenderer`.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const SCENE_BG = 0x1a1a2e;
const CELL_COLOR = 0x00ff88;
const GRID_COLOR = 0x2a2a4a;

export class Renderer3D {
  /**
   * @param {HTMLElement} container
   */
  constructor(container) {
    this._container = container;
    this._rows = 60;
    this._cols = 80;
    this._gridHelper = null;

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
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    this._scene.add(ambient);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(20, 40, 30);
    this._scene.add(dirLight);

    // InstancedMesh for alive cells (pre-allocated for max capacity)
    this._capacity = this._rows * this._cols;
    this._cellMesh = this._buildInstancedMesh(this._capacity);
    this._scene.add(this._cellMesh);
    this._cellMesh.count = 0;

    // Grid helper
    this._buildGridHelper();

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
   * @param {{ rows: number, cols: number, cells: [number, number][] }} state
   */
  update(state) {
    const { rows, cols, cells } = state;
    const sizeChanged = rows !== this._rows || cols !== this._cols;

    this._rows = rows;
    this._cols = cols;

    if (sizeChanged) {
      // Reallocate instanced mesh if grid grew
      const needed = rows * cols;
      if (needed > this._capacity) {
        this._capacity = needed;
        this._scene.remove(this._cellMesh);
        this._cellMesh.geometry.dispose();
        this._cellMesh = this._buildInstancedMesh(this._capacity);
        this._scene.add(this._cellMesh);
      }
      this._buildGridHelper();
    }

    // Position one cube per alive cell
    const dummy = new THREE.Object3D();
    const halfCols = cols / 2;
    const halfRows = rows / 2;

    let i = 0;
    for (const [r, c] of cells) {
      dummy.position.set(c - halfCols + 0.5, 0.5, r - halfRows + 0.5);
      dummy.updateMatrix();
      this._cellMesh.setMatrixAt(i, dummy.matrix);
      i++;
    }
    this._cellMesh.count = i;
    this._cellMesh.instanceMatrix.needsUpdate = true;
  }

  /** No-op — animation loop drives rendering continuously. */
  render() {}

  /** @param {boolean} value */
  setShowGridLines(value) {
    if (this._gridHelper) this._gridHelper.visible = value;
  }

  /** No-op — hover highlight not applicable in 3D view-only mode. */
  setHoverCell(_cell) {}

  /**
   * Convert screen pixel coords to grid cell via raycasting onto y=0 plane.
   * Returns null if the ray misses the plane.
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
    const mat = new THREE.MeshPhongMaterial({ color: CELL_COLOR });
    return new THREE.InstancedMesh(geo, mat, capacity);
  }

  _buildGridHelper() {
    if (this._gridHelper) {
      this._scene.remove(this._gridHelper);
      this._gridHelper.geometry?.dispose();
    }
    // GridHelper(size, divisions) — use the larger dimension as size
    const size = Math.max(this._rows, this._cols);
    const divs = size;
    this._gridHelper = new THREE.GridHelper(size, divs, GRID_COLOR, GRID_COLOR);
    this._scene.add(this._gridHelper);
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
    requestAnimationFrame(() => this._animate());
    this._controls.update();
    this._renderer.render(this._scene, this._camera);
  }
}
