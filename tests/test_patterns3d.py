"""Unit tests for 3D preset patterns."""

import pytest

from conway.patterns3d import (
    PRESET_NAMES_3D,
    center_pattern_3d,
    get_pattern_3d,
    pattern_bounds_3d,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# PRESET_NAMES_3D
# ---------------------------------------------------------------------------


def test_preset_names_not_empty():
    assert len(PRESET_NAMES_3D) >= 3


def test_expected_presets_present():
    for name in ("carter_bays_glider", "accordion", "bad_reaction"):
        assert name in PRESET_NAMES_3D


# ---------------------------------------------------------------------------
# get_pattern_3d
# ---------------------------------------------------------------------------


def test_get_pattern_3d_returns_dict_with_required_keys():
    pat = get_pattern_3d("carter_bays_glider")
    assert "birth_set" in pat
    assert "survival_set" in pat
    assert "cells" in pat


def test_get_pattern_3d_cells_are_triples():
    for name in PRESET_NAMES_3D:
        pat = get_pattern_3d(name)
        for cell in pat["cells"]:
            assert len(cell) == 3


def test_get_pattern_3d_unknown_raises():
    with pytest.raises(ValueError, match="Unknown 3D preset"):
        get_pattern_3d("does_not_exist")


def test_get_pattern_3d_birth_survival_are_frozensets():
    pat = get_pattern_3d("accordion")
    assert isinstance(pat["birth_set"], frozenset)
    assert isinstance(pat["survival_set"], frozenset)


# ---------------------------------------------------------------------------
# pattern_bounds_3d
# ---------------------------------------------------------------------------


def test_pattern_bounds_3d_empty():
    assert pattern_bounds_3d([]) == (0, 0, 0, 0, 0, 0)


def test_pattern_bounds_3d_single_cell():
    assert pattern_bounds_3d([(3, 4, 5)]) == (3, 4, 5, 3, 4, 5)


def test_pattern_bounds_3d_multiple_cells():
    cells = [(0, 0, 0), (2, 3, 4), (1, 1, 1)]
    min_l, min_r, min_c, max_l, max_r, max_c = pattern_bounds_3d(cells)
    assert min_l == 0 and max_l == 2
    assert min_r == 0 and max_r == 3
    assert min_c == 0 and max_c == 4


# ---------------------------------------------------------------------------
# center_pattern_3d
# ---------------------------------------------------------------------------


def test_center_pattern_3d_empty():
    assert center_pattern_3d([], 10, 10, 10) == []


def test_center_pattern_3d_single_cell_lands_in_centre():
    centered = center_pattern_3d([(0, 0, 0)], 10, 10, 10)
    assert len(centered) == 1
    l, r, c = centered[0]
    assert l == 4 or l == 5
    assert r == 4 or r == 5
    assert c == 4 or c == 5


def test_center_pattern_3d_all_cells_in_bounds():
    pat = get_pattern_3d("carter_bays_glider")
    centered = center_pattern_3d(pat["cells"], 21, 21, 21)
    for l, r, c in centered:
        assert 0 <= l < 21
        assert 0 <= r < 21
        assert 0 <= c < 21


def test_center_pattern_3d_count_preserved_when_pattern_fits():
    cells = [(0, 0, 0), (1, 1, 1), (2, 2, 2)]
    centered = center_pattern_3d(cells, 21, 21, 21)
    assert len(centered) == len(cells)
