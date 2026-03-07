"""WebSocket handler — GameSession + async tick loop."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from conway.game import Grid
from conway.patterns import PRESET_NAMES, center_pattern, get_pattern

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_ROWS = 60
DEFAULT_COLS = 80
DEFAULT_TPS = 5.0
MIN_TPS = 0.5
MAX_TPS = 30.0


class GameSession:
    """Manages a single client's game state and async tick loop."""

    def __init__(self, websocket: WebSocket) -> None:
        self.ws = websocket
        self.grid = Grid(rows=DEFAULT_ROWS, cols=DEFAULT_COLS)
        self.running = False
        self.tps = DEFAULT_TPS
        self._loop_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # State serialization helpers
    # ------------------------------------------------------------------

    def _state_message(self, msg_type: str = "state") -> dict[str, Any]:
        return {
            "type": msg_type,
            "generation": self.grid.generation,
            "rows": self.grid.rows,
            "cols": self.grid.cols,
            "cells": self.grid.alive_cells(),
            "running": self.running,
            "tps": self.tps,
        }

    def _init_message(self) -> dict[str, Any]:
        msg = self._state_message("init")
        msg["presets"] = PRESET_NAMES
        return msg

    async def _send(self, data: dict[str, Any]) -> None:
        await self.ws.send_text(json.dumps(data))

    async def _send_state(self) -> None:
        await self._send(self._state_message())

    async def _send_error(self, message: str) -> None:
        await self._send({"type": "error", "message": message})

    # ------------------------------------------------------------------
    # Game loop
    # ------------------------------------------------------------------

    async def _tick_loop(self) -> None:
        try:
            while True:
                interval = 1.0 / self.tps  # re-read each iteration
                await asyncio.sleep(interval)
                self.grid = self.grid.step()
                await self._send_state()
        except asyncio.CancelledError:
            pass

    def start_loop(self) -> None:
        if self._loop_task is None or self._loop_task.done():
            self._loop_task = asyncio.create_task(self._tick_loop())
        self.running = True

    async def stop_loop(self) -> None:
        self.running = False
        if self._loop_task and not self._loop_task.done():
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        self._loop_task = None

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    async def handle_play(self, _msg: dict) -> None:
        if not self.running:
            self.start_loop()
            await self._send_state()

    async def handle_pause(self, _msg: dict) -> None:
        if self.running:
            await self.stop_loop()
            await self._send_state()

    async def handle_step(self, _msg: dict) -> None:
        was_running = self.running
        if was_running:
            await self.stop_loop()
        self.grid = self.grid.step()
        await self._send_state()

    async def handle_clear(self, _msg: dict) -> None:
        await self.stop_loop()
        self.grid = self.grid.clear()
        await self._send_state()

    async def handle_set_speed(self, msg: dict) -> None:
        tps = msg.get("tps")
        if tps is None or not isinstance(tps, (int, float)):
            await self._send_error("set_speed requires numeric 'tps'")
            return
        self.tps = max(MIN_TPS, min(MAX_TPS, float(tps)))
        await self._send_state()

    async def handle_toggle_cell(self, msg: dict) -> None:
        row, col = msg.get("row"), msg.get("col")
        if row is None or col is None:
            await self._send_error("toggle_cell requires 'row' and 'col'")
            return
        self.grid = self.grid.toggle_cell(int(row), int(col))
        await self._send_state()

    async def handle_set_cells(self, msg: dict) -> None:
        cells = msg.get("cells")
        alive = msg.get("alive", True)
        if not isinstance(cells, list):
            await self._send_error("set_cells requires 'cells' list")
            return
        self.grid = self.grid.set_cells([tuple(c) for c in cells], bool(alive))
        await self._send_state()

    async def handle_load_preset(self, msg: dict) -> None:
        name = msg.get("name", "")
        try:
            pattern = get_pattern(name)
        except ValueError as exc:
            await self._send_error(str(exc))
            return
        was_running = self.running
        if was_running:
            await self.stop_loop()
        centered = center_pattern(pattern, self.grid.rows, self.grid.cols)
        self.grid = Grid(
            rows=self.grid.rows,
            cols=self.grid.cols,
            alive=centered,
            generation=0,
        )
        if was_running:
            self.start_loop()
        await self._send_state()

    async def handle_resize(self, msg: dict) -> None:
        rows = msg.get("rows", DEFAULT_ROWS)
        cols = msg.get("cols", DEFAULT_COLS)
        try:
            rows, cols = int(rows), int(cols)
        except (TypeError, ValueError):
            await self._send_error("resize requires integer 'rows' and 'cols'")
            return
        if rows < 5 or cols < 5 or rows > 200 or cols > 300:
            await self._send_error("resize: dimensions out of range (5-200 rows, 5-300 cols)")
            return
        self.grid = self.grid.resize(rows, cols)
        await self._send_state()

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    _HANDLERS = {
        "play": handle_play,
        "pause": handle_pause,
        "step": handle_step,
        "clear": handle_clear,
        "set_speed": handle_set_speed,
        "toggle_cell": handle_toggle_cell,
        "set_cells": handle_set_cells,
        "load_preset": handle_load_preset,
        "resize": handle_resize,
    }

    async def dispatch(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON")
            return

        msg_type = msg.get("type", "")
        handler = self._HANDLERS.get(msg_type)
        if handler is None:
            await self._send_error(f"Unknown message type: {msg_type!r}")
            return
        await handler(self, msg)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def run(self) -> None:
        await self.ws.accept()
        await self._send(self._init_message())
        try:
            while True:
                data = await self.ws.receive_text()
                await self.dispatch(data)
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        finally:
            await self.stop_loop()


# ------------------------------------------------------------------
# Route
# ------------------------------------------------------------------


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    session = GameSession(websocket)
    await session.run()
