/**
 * Entry point — wires WSClient, Renderer, Controls together.
 * Handles draw mode (mousedown + drag) and keyboard shortcuts.
 */

import { WSClient } from './ws_client.js';
import { Renderer } from './renderer.js';
import { Controls } from './controls.js';

// ------------------------------------------------------------------
// Init
// ------------------------------------------------------------------

const canvas = document.getElementById('game-canvas');
const renderer = new Renderer(canvas);

const wsUrl = `ws://${location.host}/ws`;
const ws = new WSClient(wsUrl, {
  onInit(msg) {
    renderer.update(msg);
    controls.populatePresets(msg.presets ?? []);
    controls.updateStatus(msg);
    // Sync speed slider with server's default
    const slider = document.getElementById('speed-slider');
    const label = document.getElementById('speed-label');
    if (slider) slider.value = msg.tps;
    if (label) label.textContent = `${msg.tps} TPS`;
  },
  onState(msg) {
    renderer.update(msg);
    controls.updateStatus(msg);
  },
  onError(msg) {
    console.warn('Server error:', msg.message);
  },
});

const controls = new Controls(ws, renderer);

// ------------------------------------------------------------------
// Draw mode
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
  const cell = renderer.pixelToCell(e.offsetX, e.offsetY);
  pendingCells.push([cell.row, cell.col]);
});

canvas.addEventListener('mousemove', (e) => {
  const cell = renderer.pixelToCell(e.offsetX, e.offsetY);
  renderer.setHoverCell(cell);
  renderer.render();

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
  renderer.setHoverCell(null);
  renderer.render();
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
