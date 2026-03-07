/**
 * Entry point — wires WSClient, Renderer, Renderer3D, Controls together.
 * Handles draw mode (mousedown + drag), keyboard shortcuts, and 2D/3D toggle.
 */

import { WSClient } from './ws_client.js';
import { Renderer } from './renderer.js';
import { Renderer3D } from './renderer3d.js';
import { Controls } from './controls.js';

// ------------------------------------------------------------------
// Init
// ------------------------------------------------------------------

const canvas = document.getElementById('game-canvas');
const threeContainer = document.getElementById('three-container');

const renderer2d = new Renderer(canvas);

// Renderer3D is created lazily on first switch to 3D so the container
// already has real dimensions (clientWidth/Height > 0).
let renderer3d = null;

let activeRenderer = renderer2d;
let lastState = null; // most recent state message, for re-render on view switch

// ------------------------------------------------------------------
// Preset loading toast
// ------------------------------------------------------------------

const presetToast = document.getElementById('preset-toast');
let presetPending = false;
let toastTimer = null;

function showToast(text, autoHide = false) {
  if (!presetToast) return;
  presetToast.textContent = text;
  presetToast.classList.add('visible');
  clearTimeout(toastTimer);
  if (autoHide) {
    toastTimer = setTimeout(() => presetToast.classList.remove('visible'), 1500);
  }
}

function hideToast() {
  if (!presetToast) return;
  clearTimeout(toastTimer);
  presetToast.classList.remove('visible');
}

// ------------------------------------------------------------------
// WebSocket
// ------------------------------------------------------------------

const wsUrl = `ws://${location.host}/ws`;
const ws = new WSClient(wsUrl, {
  onInit(msg) {
    lastState = msg;
    activeRenderer.update(msg);
    controls.populatePresets(msg.presets ?? []);
    controls.updateStatus(msg);
    // Sync speed slider with server's default
    const slider = document.getElementById('speed-slider');
    const label = document.getElementById('speed-label');
    if (slider) slider.value = msg.tps;
    if (label) label.textContent = `${msg.tps} TPS`;
  },
  onState(msg) {
    lastState = msg;
    activeRenderer.update(msg);
    controls.updateStatus(msg);
    if (presetPending) {
      presetPending = false;
      showToast('Loaded ✓', true);
    }
  },
  onError(msg) {
    console.warn('Server error:', msg.message);
    presetPending = false;
    hideToast();
  },
});

const controls = new Controls(ws, renderer2d);

// ------------------------------------------------------------------
// Intercept Load button to drive the toast
// ------------------------------------------------------------------

document.getElementById('btn-load-preset')?.addEventListener('click', () => {
  const sel = document.getElementById('preset-select');
  if (sel && sel.value) {
    presetPending = true;
    showToast('Loading…');
  }
});

// ------------------------------------------------------------------
// 2D / 3D view toggle
// ------------------------------------------------------------------

const btn2d = document.getElementById('btn-view-2d');
const btn3d = document.getElementById('btn-view-3d');

function switchTo2D() {
  activeRenderer = renderer2d;
  canvas.style.display = '';
  threeContainer.style.display = 'none';
  btn2d.classList.add('active');
  btn3d.classList.remove('active');
  if (lastState) renderer2d.update(lastState);
}

function switchTo3D() {
  canvas.style.display = 'none';
  threeContainer.style.display = '';    // show first so dimensions are non-zero
  btn3d.classList.add('active');
  btn2d.classList.remove('active');

  // Lazy-init: create Renderer3D only now, when the container is visible
  if (!renderer3d) {
    renderer3d = new Renderer3D(threeContainer);
    // Sync grid-lines checkbox state
    const chk = document.getElementById('chk-gridlines');
    if (chk) renderer3d.setShowGridLines(chk.checked);
  }

  activeRenderer = renderer3d;
  if (lastState) renderer3d.update(lastState);
}

btn2d?.addEventListener('click', switchTo2D);
btn3d?.addEventListener('click', switchTo3D);

// Grid lines: controls.js handles renderer2d; this listener covers renderer3d
document.getElementById('chk-gridlines')?.addEventListener('change', (e) => {
  renderer3d?.setShowGridLines(e.target.checked);
});

// ------------------------------------------------------------------
// Draw mode (2D canvas only)
// ------------------------------------------------------------------

let drawing = false;
let drawAlive = true; // current draw mode (alive or dead)
let pendingCells = []; // accumulated during drag

function getDrawMode() {
  // Check which draw button is active
  const btn = document.querySelector('#btn-draw-dead.active');
  return btn ? false : true;
}

// Draw mode toggle buttons
document.getElementById('btn-draw-alive')?.addEventListener('click', () => {
  document.getElementById('btn-draw-alive').classList.add('active');
  document.getElementById('btn-draw-dead').classList.remove('active');
  drawAlive = true;
});

document.getElementById('btn-draw-dead')?.addEventListener('click', () => {
  document.getElementById('btn-draw-dead').classList.add('active');
  document.getElementById('btn-draw-alive').classList.remove('active');
  drawAlive = false;
});

canvas.addEventListener('mousedown', (e) => {
  if (e.button !== 0) return;
  drawing = true;
  drawAlive = getDrawMode();
  pendingCells = [];
  const cell = renderer2d.pixelToCell(e.offsetX, e.offsetY);
  pendingCells.push([cell.row, cell.col]);
});

canvas.addEventListener('mousemove', (e) => {
  const cell = renderer2d.pixelToCell(e.offsetX, e.offsetY);
  renderer2d.setHoverCell(cell);
  renderer2d.render();

  if (!drawing) return;
  pendingCells.push([cell.row, cell.col]);

  // Flush accumulated cells on drag
  if (pendingCells.length >= 4) {
    ws.setCells(pendingCells, drawAlive);
    pendingCells = [];
  }
});

canvas.addEventListener('mouseup', () => {
  if (!drawing) return;
  drawing = false;
  if (pendingCells.length === 1) {
    // Single click — toggle
    const [row, col] = pendingCells[0];
    ws.toggleCell(row, col);
  } else if (pendingCells.length > 1) {
    ws.setCells(pendingCells, drawAlive);
  }
  pendingCells = [];
});

canvas.addEventListener('mouseleave', () => {
  renderer2d.setHoverCell(null);
  renderer2d.render();
  if (drawing) {
    drawing = false;
    if (pendingCells.length > 0) {
      ws.setCells(pendingCells, drawAlive);
      pendingCells = [];
    }
  }
});

// ------------------------------------------------------------------
// Keyboard shortcuts
// ------------------------------------------------------------------

document.addEventListener('keydown', (e) => {
  // Ignore when focus is in an input/select
  const tag = document.activeElement?.tagName ?? '';
  if (['INPUT', 'SELECT', 'TEXTAREA'].includes(tag)) return;

  switch (e.key) {
    case ' ':
      e.preventDefault();
      document.getElementById('btn-play-pause')?.click();
      break;
    case 'ArrowRight':
      e.preventDefault();
      ws.step();
      break;
    case 'c':
    case 'C':
      ws.clear();
      break;
  }
});
