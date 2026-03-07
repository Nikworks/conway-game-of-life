# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Conway's Game of Life — Python FastAPI backend streaming game state over WebSockets to a vanilla HTML5 Canvas frontend.

## Commands

```bash
# Install dependencies (creates .venv)
uv sync

# Run server (http://localhost:8000)
uv run uvicorn conway.app:app --reload --port 8000

# Run all tests
uv run pytest

# Run tests with verbose output
uv run pytest -v

# Run a single test file
uv run pytest tests/test_game.py -v

# Run a single test by name
uv run pytest -k "test_blinker" -v
```

**Note:** The project directory contains `:` in the path (`AI:Run - Retreat`). If `uv run` fails with "path segment contains separator", use `.venv/bin/python -m pytest` directly:
```bash
.venv/bin/python -m pytest -v
```

## Architecture

### Stack
- **Backend:** Python 3.11+, FastAPI, WebSockets (async game loop)
- **Frontend:** Vanilla HTML5/CSS/JS, Canvas rendering (no framework, no bundler)
- **Tests:** pytest + pytest-asyncio

### Project Structure
```
src/conway/
├── game.py         # Grid class — sparse set representation, immutable step()
├── patterns.py     # 10 preset patterns + center_pattern() utility
├── app.py          # FastAPI factory, StaticFiles at /static, GET / → index.html
└── ws_handler.py   # GameSession + async tick loop, all protocol handlers

static/
├── index.html
├── css/style.css   # Dark theme, responsive
└── js/
    ├── main.js     # Entry point, draw mode, keyboard shortcuts
    ├── renderer.js # Canvas renderer
    ├── ws_client.js # WebSocket client with auto-reconnect
    └── controls.js  # UI control bindings

tests/
├── test_game.py         # ~22 unit tests for Grid
├── test_patterns.py     # ~10 tests for patterns + centering
└── test_ws_protocol.py  # ~14 integration tests via TestClient
```

### Grid (`game.py`)
- Alive cells stored as `frozenset[tuple[int, int]]` (sparse)
- Default: 60 rows × 80 cols, finite non-wrapping boundaries
- `step()` is immutable — returns new `Grid`, does not mutate
- Candidate-based neighbor counting for efficiency

### WebSocket Protocol
Each browser tab gets its own `GameSession` (isolated state).

**Client → Server:** `play`, `pause`, `step`, `clear`, `set_speed`, `toggle_cell`, `set_cells`, `load_preset`, `resize`

**Server → Client:** `init` (on connect), `state` (after every mutation/tick), `error`

### Presets (10 total)
`glider`, `blinker`, `toad`, `beacon`, `pulsar`, `pentadecathlon`, `gosper_glider_gun`, `r_pentomino`, `diehard`, `acorn`

## Key Pitfalls
- Python `set` is not JSON-serializable — always use `grid.alive_cells()` (returns list)
- `cells` in JSON are lists-of-lists; `Grid.from_dict()` handles the conversion
- Use `uv run` (sets PYTHONPATH via src layout); do not run `python src/conway/app.py` directly
- WebSocket URL must be `ws://` for local dev (not `wss://`)
- Canvas mouse: use `offsetX`/`offsetY`, not `clientX`/`clientY`
