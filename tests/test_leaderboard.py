"""Integration tests for the Hall of Fame leaderboard."""

import json
import pytest
import pytest_asyncio

from conway.leaderboard import DB_PATH, get_leaderboard, init_db, save_score

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Fixture: fresh in-memory DB for each test
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def temp_db(tmp_path, monkeypatch):
    """Redirect DB_PATH to a temp file so tests don't share state."""
    db_file = tmp_path / "test_hof.db"
    monkeypatch.setattr("conway.leaderboard.DB_PATH", db_file)
    await init_db()
    yield db_file


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------


async def test_init_db_creates_table(temp_db):
    import aiosqlite
    async with aiosqlite.connect(temp_db) as db:
        cur = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scores'"
        )
        row = await cur.fetchone()
    assert row is not None


# ---------------------------------------------------------------------------
# save_score
# ---------------------------------------------------------------------------


async def test_save_score_returns_dict():
    saved = await save_score("Alice", "glider", 100, 5, "[]")
    assert saved["player_name"] == "Alice"
    assert saved["generation"] == 100
    assert saved["id"] is not None


async def test_save_score_null_preset():
    saved = await save_score("Bob", None, 200, 10, "[]")
    assert saved["preset_used"] is None


# ---------------------------------------------------------------------------
# get_leaderboard
# ---------------------------------------------------------------------------


async def test_get_leaderboard_empty():
    rows = await get_leaderboard()
    assert rows == []


async def test_get_leaderboard_sorted_by_generation_desc():
    await save_score("P1", None, 50,  3, "[]")
    await save_score("P2", None, 200, 8, "[]")
    await save_score("P3", None, 10,  1, "[]")
    rows = await get_leaderboard()
    gens = [r["generation"] for r in rows]
    assert gens == sorted(gens, reverse=True)


async def test_get_leaderboard_top_10_limit():
    for i in range(15):
        await save_score(f"P{i}", None, i * 10, i, "[]")
    rows = await get_leaderboard(limit=10)
    assert len(rows) == 10
    # Top entry should be the highest generation
    assert rows[0]["generation"] == 140


async def test_get_leaderboard_includes_expected_fields():
    await save_score("Charlie", "acorn", 5206, 633, "[[1,2]]")
    rows = await get_leaderboard()
    assert len(rows) == 1
    r = rows[0]
    for field in ("id", "player_name", "preset_used", "generation", "alive_count", "saved_at"):
        assert field in r
