"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from conway.ws_handler import router as ws_router

STATIC_DIR = Path(__file__).parent.parent.parent / "static"


def create_app() -> FastAPI:
    application = FastAPI(title="Conway's Game of Life")

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

    return application


app = create_app()
