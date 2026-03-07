# Conway's Game of Life

A fully-featured Conway's Game of Life web app with a Python FastAPI backend streaming game state over WebSockets to a vanilla HTML5 Canvas frontend.

## Features

- Real-time game state streaming via WebSockets
- Play / Pause / Step controls
- Variable speed (ticks per second)
- Live cell drawing by clicking or dragging on the canvas
- 10 preset patterns: Glider, Blinker, Toad, Beacon, Pulsar, Pentadecathlon, Gosper Glider Gun, R-Pentomino, Diehard, Acorn
- Grid-lines toggle
- Status bar: generation, alive cell count, TPS
- Keyboard shortcuts: `Space` = play/pause, `→` = step, `C` = clear
- Dark theme, responsive layout

## Stack

- **Backend:** Python 3.11+, FastAPI, WebSockets (async game loop via asyncio)
- **Frontend:** Vanilla HTML5/CSS/JS with Canvas rendering (no framework, no bundler)
- **Tests:** pytest + pytest-asyncio

## Quick Start

```bash
# Install uv (if not present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run server
uv run uvicorn conway.app:app --reload --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## Development

```bash
# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_game.py -v

# Run a specific test
uv run pytest -k "test_blinker" -v
```

## WebSocket Protocol

Each browser tab gets its own independent game session.

**Client → Server messages:**
```json
{ "type": "play" }
{ "type": "pause" }
{ "type": "step" }
{ "type": "clear" }
{ "type": "set_speed", "tps": 5.0 }
{ "type": "toggle_cell", "row": 12, "col": 34 }
{ "type": "set_cells", "cells": [[12,34],[12,35]], "alive": true }
{ "type": "load_preset", "name": "glider" }
{ "type": "resize", "rows": 60, "cols": 80 }
```

**Server → Client messages:**
```json
// On connect
{ "type": "init", "generation": 0, "rows": 60, "cols": 80,
  "cells": [], "running": false, "tps": 5.0, "presets": [...] }

// After every tick/step/mutation
{ "type": "state", "generation": 42, "rows": 60, "cols": 80,
  "cells": [[r,c],...], "running": true, "tps": 5.0 }

{ "type": "error", "message": "Unknown preset: 'foo'" }
```

## Architecture

- `Grid` stores alive cells as `set[tuple[int, int]]` (sparse representation)
- Default grid: 60 rows × 80 cols, finite/non-wrapping
- `step()` is immutable — returns a new `Grid`
- Each WebSocket connection is an independent `GameSession`
- Game loop runs as an `asyncio.Task`
