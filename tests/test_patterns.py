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

pytestmark = pytest.mark.unit


def test_all_presets_exist():
    expected = {
        "glider", "blinker", "toad", "beacon", "pulsar",
        "pentadecathlon", "gosper_glider_gun", "r_pentomino",
        "diehard", "acorn",
        "herschel", "t_pentomino", "brain",
    }
    assert set(PRESET_NAMES) == expected


def test_get_pattern_known():
    result = get_pattern("glider")
    assert isinstance(result, list)
    assert len(result) > 0


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


@pytest.mark.parametrize("name,pattern", list(PATTERNS.items()))
def test_center_pattern_in_bounds(name, pattern):
    centered = center_pattern(pattern, 60, 80)
    for r, c in centered:
        assert 0 <= r < 60, f"{name}: row {r} out of bounds"
        assert 0 <= c < 80, f"{name}: col {c} out of bounds"


def test_center_pattern_glider():
    # Glider (3x3 bounding box) centered on 60x80:
    # offset_r = (60-3)//2 = 28, offset_c = (80-3)//2 = 38
    p = get_pattern("glider")
    result = center_pattern(p, 60, 80)
    assert set(result) == {(28, 39), (29, 40), (30, 38), (30, 39), (30, 40)}


def test_center_pattern_empty():
    assert center_pattern([], 60, 80) == []


def test_gosper_gun_has_enough_room():
    p = get_pattern("gosper_glider_gun")
    centered = center_pattern(p, 60, 80)
    assert len(centered) == len(p)  # no cells clipped


def test_load_pattern_into_grid():
    pattern = get_pattern("blinker")
    centered = center_pattern(pattern, 20, 20)
    g = Grid(rows=20, cols=20, alive=centered)
    assert g.count() == 3


def test_gosper_gun_grows():
    """After enough steps the Gosper gun should produce more live cells."""
    pattern = get_pattern("gosper_glider_gun")
    centered = center_pattern(pattern, 60, 80)
    g = Grid(rows=60, cols=80, alive=centered)
    initial_count = g.count()
    for _ in range(35):
        g = g.step()
    assert g.count() > initial_count
