"""SQLite-backed Hall of Fame leaderboard."""

from __future__ import annotations

import json
from pathlib import Path

import aiosqlite

DB_PATH = Path("hall_of_fame.db")


async def init_db() -> None:
    """Create the scores table if it does not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT    NOT NULL,
                preset_used TEXT,
                generation  INTEGER NOT NULL,
                alive_count INTEGER NOT NULL,
                cells_json  TEXT    NOT NULL,
                saved_at    TEXT    DEFAULT (datetime('now'))
            )
            """
        )
        await db.commit()


async def save_score(
    player_name: str,
    preset_used: str | None,
    generation: int,
    alive_count: int,
    cells_json: str,
) -> dict:
    """Insert a score and return the saved row as a dict."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO scores (player_name, preset_used, generation, alive_count, cells_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (player_name, preset_used, generation, alive_count, cells_json),
        )
        await db.commit()
        row_id = cursor.lastrowid

    return {
        "id": row_id,
        "player_name": player_name,
        "preset_used": preset_used,
        "generation": generation,
        "alive_count": alive_count,
    }


async def get_leaderboard(limit: int = 10) -> list[dict]:
    """Return up to `limit` scores ordered by generation descending."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT id, player_name, preset_used, generation, alive_count, saved_at
            FROM scores
            ORDER BY generation DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]
