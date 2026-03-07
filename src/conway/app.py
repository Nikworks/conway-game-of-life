"""FastAPI application factory."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from conway.leaderboard import get_leaderboard, init_db, save_score
from conway.ws_handler import router as ws_router

STATIC_DIR = Path(__file__).parent.parent.parent / "static"


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db()
    yield


class ScoreIn(BaseModel):
    player_name: str
    preset_used: str | None = None
    generation: int
    alive_count: int
    cells: list


def create_app() -> FastAPI:
    application = FastAPI(title="Conway's Game of Life", lifespan=lifespan)

    # WebSocket routes
    application.include_router(ws_router)

    # Serve static files (CSS, JS)
    application.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

    @application.get("/")
    async def index() -> FileResponse:
        return FileResponse(str(STATIC_DIR / "index.html"))

    @application.get("/api/leaderboard")
    async def leaderboard() -> JSONResponse:
        rows = await get_leaderboard()
        return JSONResponse(rows)

    @application.post("/api/scores")
    async def post_score(score: ScoreIn) -> JSONResponse:
        cells_json = json.dumps(score.cells)
        saved = await save_score(
            player_name=score.player_name,
            preset_used=score.preset_used,
            generation=score.generation,
            alive_count=score.alive_count,
            cells_json=cells_json,
        )
        return JSONResponse(saved, status_code=201)

    return application


app = create_app()
