/**
 * Canvas renderer for Conway's Game of Life.
 * Draws the grid and alive cells.
 */

const COLORS = {
  background: '#0f1117',
  cell: '#5b7cf7',
  gridLine: 'rgba(255,255,255,0.04)',
  cellHover: 'rgba(91,124,247,0.35)',
};

export class Renderer {
  /**
   * @param {HTMLCanvasElement} canvas
   */
  constructor(canvas) {
    this._canvas = canvas;
    this._ctx = canvas.getContext('2d');
    this._rows = 60;
    this._cols = 80;
    this._alive = new Set(); // "r,c" strings for O(1) lookup
    this._showGridLines = true;
    this._hoverCell = null; // { row, col } | null

    this._resize();
    window.addEventListener('resize', () => this._resize());
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  setShowGridLines(value) {
    this._showGridLines = value;
    this.render();
  }

  setHoverCell(cell) {
    this._hoverCell = cell;
  }

  /**
   * Update state from a server message and redraw.
   * @param {{ rows: number, cols: number, cells: [number, number][] }} state
   */
  update(state) {
    this._rows = state.rows;
    this._cols = state.cols;
    this._alive = new Set(state.cells.map(([r, c]) => `${r},${c}`));
    this._resize();
    this.render();
  }

  render() {
    const ctx = this._ctx;
    const { width, height } = this._canvas;
    const cellW = width / this._cols;
    const cellH = height / this._rows;

    // Background
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, width, height);

    // Alive cells
    ctx.fillStyle = COLORS.cell;
    for (const key of this._alive) {
      const [r, c] = key.split(',').map(Number);
      ctx.fillRect(
        Math.floor(c * cellW),
        Math.floor(r * cellH),
        Math.ceil(cellW),
        Math.ceil(cellH),
      );
    }

    // Hover highlight
    if (this._hoverCell) {
      const { row, col } = this._hoverCell;
      ctx.fillStyle = COLORS.cellHover;
      ctx.fillRect(
        Math.floor(col * cellW),
        Math.floor(row * cellH),
        Math.ceil(cellW),
        Math.ceil(cellH),
      );
    }

    // Grid lines
    if (this._showGridLines) {
      ctx.strokeStyle = COLORS.gridLine;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let c = 0; c <= this._cols; c++) {
        const x = Math.floor(c * cellW) + 0.5;
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
      }
      for (let r = 0; r <= this._rows; r++) {
        const y = Math.floor(r * cellH) + 0.5;
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
      }
      ctx.stroke();
    }
  }

  /**
   * Convert canvas pixel coordinates to grid cell.
   * @param {number} offsetX
   * @param {number} offsetY
   * @returns {{ row: number, col: number }}
   */
  pixelToCell(offsetX, offsetY) {
    const cellW = this._canvas.width / this._cols;
    const cellH = this._canvas.height / this._rows;
    return {
      row: Math.floor(offsetY / cellH),
      col: Math.floor(offsetX / cellW),
    };
  }

  // ------------------------------------------------------------------
  // Internal
  // ------------------------------------------------------------------

  _resize() {
    const container = this._canvas.parentElement;
    if (!container) return;

    const maxW = container.clientWidth - 16;
    const maxH = container.clientHeight - 16;

    // Maintain aspect ratio cols:rows
    const aspect = this._cols / this._rows;
    let w = maxW;
    let h = w / aspect;
    if (h > maxH) {
      h = maxH;
      w = h * aspect;
    }

    this._canvas.width = Math.floor(w);
    this._canvas.height = Math.floor(h);
    this.render();
  }
}
