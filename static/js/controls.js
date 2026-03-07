/**
 * UI control bindings for Conway's Game of Life.
 * Wires DOM events to WSClient calls and updates status display.
 */

export class Controls {
  /**
   * @param {import('./ws_client.js').WSClient} ws
   * @param {import('./renderer.js').Renderer} renderer
   */
  constructor(ws, renderer) {
    this._ws = ws;
    this._renderer = renderer;
    this._running = false;
    this._presets = [];

    this._bindButtons();
    this._bindSpeed();
    this._bindPresets();
    this._bindGridLines();
  }

  // ------------------------------------------------------------------
  // Called by main.js when server sends state
  // ------------------------------------------------------------------

  updateStatus(state) {
    this._running = state.running;

    // Play/Pause button label
    const btn = document.getElementById('btn-play-pause');
    if (btn) {
      btn.textContent = state.running ? '⏸ Pause' : '▶ Play';
      btn.classList.toggle('primary', !state.running);
    }

    document.getElementById('stat-generation').textContent = state.generation;
    document.getElementById('stat-alive').textContent =
      (state.cells ?? []).length;
    document.getElementById('stat-tps').textContent =
      Number(state.tps).toFixed(1);
    document.getElementById('stat-status').textContent =
      state.running ? 'Running' : 'Paused';
  }

  populatePresets(presets) {
    this._presets = presets;
    const sel = document.getElementById('preset-select');
    if (!sel) return;
    presets.forEach((name) => {
      const opt = document.createElement('option');
      opt.value = name;
      opt.textContent = name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
      sel.appendChild(opt);
    });
  }

  // ------------------------------------------------------------------
  // Bindings
  // ------------------------------------------------------------------

  _bindButtons() {
    document.getElementById('btn-play-pause')?.addEventListener('click', () => {
      this._running ? this._ws.pause() : this._ws.play();
    });

    document.getElementById('btn-step')?.addEventListener('click', () => {
      this._ws.step();
    });

    document.getElementById('btn-clear')?.addEventListener('click', () => {
      this._ws.clear();
    });
  }

  _bindSpeed() {
    const slider = document.getElementById('speed-slider');
    const label = document.getElementById('speed-label');
    if (!slider) return;

    slider.addEventListener('input', () => {
      const tps = parseFloat(slider.value);
      if (label) label.textContent = `${tps} TPS`;
      this._ws.setSpeed(tps);
    });
  }

  _bindPresets() {
    document.getElementById('btn-load-preset')?.addEventListener('click', () => {
      const sel = document.getElementById('preset-select');
      if (sel && sel.value) {
        this._ws.loadPreset(sel.value);
      }
    });

    // Also load on double-click of select
    document.getElementById('preset-select')?.addEventListener('dblclick', () => {
      const sel = document.getElementById('preset-select');
      if (sel && sel.value) {
        this._ws.loadPreset(sel.value);
      }
    });
  }

  _bindGridLines() {
    document.getElementById('chk-gridlines')?.addEventListener('change', (e) => {
      this._renderer.setShowGridLines(e.target.checked);
    });
  }
}
