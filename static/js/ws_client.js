/**
 * WebSocket client for Conway's Game of Life.
 * Manages the connection and provides send helpers.
 */

export class WSClient {
  /**
   * @param {string} url - WebSocket URL (ws://...)
   * @param {object} handlers - { onInit, onState, onError, onClose }
   */
  constructor(url, handlers = {}) {
    this._url = url;
    this._handlers = handlers;
    this._ws = null;
    this._reconnectDelay = 1000;
    this._connect();
  }

  _connect() {
    this._ws = new WebSocket(this._url);

    this._ws.addEventListener('open', () => {
      console.log('[WS] connected');
      this._reconnectDelay = 1000;
    });

    this._ws.addEventListener('message', (evt) => {
      let msg;
      try {
        msg = JSON.parse(evt.data);
      } catch {
        console.warn('[WS] received non-JSON message', evt.data);
        return;
      }

      switch (msg.type) {
        case 'init':
          this._handlers.onInit?.(msg);
          break;
        case 'state':
          this._handlers.onState?.(msg);
          break;
        case 'error':
          console.warn('[WS] server error:', msg.message);
          this._handlers.onError?.(msg);
          break;
        default:
          console.warn('[WS] unknown message type:', msg.type);
      }
    });

    this._ws.addEventListener('close', (evt) => {
      console.log('[WS] closed', evt.code);
      this._handlers.onClose?.(evt);
      // Auto-reconnect after delay
      setTimeout(() => this._connect(), this._reconnectDelay);
      this._reconnectDelay = Math.min(this._reconnectDelay * 1.5, 10000);
    });

    this._ws.addEventListener('error', (evt) => {
      console.error('[WS] error', evt);
    });
  }

  _send(data) {
    if (this._ws && this._ws.readyState === WebSocket.OPEN) {
      this._ws.send(JSON.stringify(data));
    } else {
      console.warn('[WS] not connected, dropping message', data.type);
    }
  }

  play()  { this._send({ type: 'play' }); }
  pause() { this._send({ type: 'pause' }); }
  step()  { this._send({ type: 'step' }); }
  clear() { this._send({ type: 'clear' }); }

  setSpeed(tps)  { this._send({ type: 'set_speed', tps }); }
  loadPreset(name) { this._send({ type: 'load_preset', name }); }
  resize(rows, cols) { this._send({ type: 'resize', rows, cols }); }

  toggleCell(row, col) {
    this._send({ type: 'toggle_cell', row, col });
  }

  setCells(cells, alive) {
    this._send({ type: 'set_cells', cells, alive });
  }

  fillRandom(density) {
    this._send({ type: 'fill_random', density });
  }
}
