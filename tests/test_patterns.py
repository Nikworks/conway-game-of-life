"""Tests for patterns and centering utilities."""

import pytest
from conway.patterns import (
    PATTERNS,
    PRESET_NAMES,
    center_pattern,
    get_pattern,
    pattern_bounds,
)
from conway.game import Grid


def test_all_presets_exist():
    expected = {
        "glider", "blinker", "toad", "beacon", "pulsar",
        "pentadecathlon", "gosper_glider_gun", "r_pentomino",
        "diehard", "acorn",
    }
    assert set(PRESET_NAMES) == expected


def test_get_pattern_known():
    p = get_pattern("glider")
    assert isinstance(p, list)
    assert len(p) > 0


def test_get_pattern_unknown():
    with pytest.raises(ValueError, match="Unknown preset"):
        get_pattern("nonexistent_pattern")


def test_pattern_bounds_glider():
    p = get_pattern("glider")
    min_r, min_c, max_r, max_c = pattern_bounds(p)
    assert min_r == 0
    assert min_c == 0
    assert max_r >= 1
    assert max_c >= 1


def test_pattern_bounds_empty():
    assert pattern_bounds([]) == (0, 0, 0, 0)


def test_center_pattern_in_bounds():
    """Centered pattern must fit within grid bounds."""
    for name, pattern in PATTERNS.items():
        centered = center_pattern(pattern, 60, 80)
        for r, c in centered:
            assert 0 <= r < 60, f"{name}: row {r} out of bounds"
            assert 0 <= c < 80, f"{name}: col {c} out of bounds"


def test_center_pattern_glider():
    p = get_pattern("glider")
    centered = center_pattern(p, 60, 80)
    rows = [r for r, _ in centered]
    cols = [c for _, c in centered]
    # Should be roughly centered
    assert min(rows) >= 25 and max(rows) < 35
    assert min(cols) >= 35 and max(cols) < 45


def test_center_pattern_empty():
    assert center_pattern([], 60, 80) == []


def test_gosper_gun_has_enough_room():
    """Gosper gun is wide — must fit in 60x80 grid."""
    p = get_pattern("gosper_glider_gun")
    centered = center_pattern(p, 60, 80)
    assert len(centered) == len(p)  # no cells clipped


def test_load_pattern_into_grid():
    from conway.patterns import center_pattern, get_pattern
    pattern = get_pattern("blinker")
    centered = center_pattern(pattern, 20, 20)
    g = Grid(rows=20, cols=20, alive=centered)
    assert g.count() == 3
    # Blinker oscillates with period 2
    g2 = g.step()
    g3 = g2.step()
    assert set(g3.alive_cells()) == set(g.alive_cells())


def test_gosper_gun_grows():
    """After enough steps the Gosper gun should produce more live cells."""
    from conway.patterns import center_pattern, get_pattern
    pattern = get_pattern("gosper_glider_gun")
    centered = center_pattern(pattern, 60, 80)
    g = Grid(rows=60, cols=80, alive=centered)
    initial_count = g.count()
    for _ in range(35):
        g = g.step()
    # Gun should have emitted at least one glider
    assert g.count() > initial_count
