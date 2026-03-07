"""Tests for core Grid game logic."""

import pytest
from conway.game import Grid

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def alive(*cells: tuple[int, int]) -> Grid:
    """Create a 20x20 grid with the given alive cells."""
    return Grid(rows=20, cols=20, alive=cells)


# ---------------------------------------------------------------------------
# Basic cell ops
# ---------------------------------------------------------------------------


def test_empty_grid():
    g = Grid()
    assert g.count() == 0
    assert g.alive_cells() == []


def test_toggle_cell_kills_alive_cell():
    g = alive((5, 5))
    result = g.toggle_cell(5, 5)
    assert not result.is_alive(5, 5)


def test_toggle_cell_revives_dead_cell():
    g = Grid(rows=20, cols=20)
    result = g.toggle_cell(5, 5)
    assert result.is_alive(5, 5)


def test_set_cells_alive():
    g = Grid(rows=10, cols=10)
    result = g.set_cells([(1, 1), (2, 2), (3, 3)], alive=True)
    assert result.count() == 3


def test_set_cells_dead():
    g = alive((1, 1), (2, 2), (3, 3))
    result = g.set_cells([(1, 1), (3, 3)], alive=False)
    assert result.count() == 1
    assert result.is_alive(2, 2)


def test_clear():
    g = alive((1, 1), (2, 2))
    result = g.clear()
    assert result.count() == 0
    assert result.rows == g.rows


# ---------------------------------------------------------------------------
# Conway rules: underpopulation
# ---------------------------------------------------------------------------


def test_underpopulation_0_neighbors_dies():
    g = alive((5, 5))
    result = g.step()
    assert not result.is_alive(5, 5)


def test_underpopulation_1_neighbor_dies():
    g = alive((5, 5), (5, 6))
    result = g.step()
    assert not result.is_alive(5, 5)
    assert not result.is_alive(5, 6)


# ---------------------------------------------------------------------------
# Conway rules: survival
# ---------------------------------------------------------------------------


def test_survival_2_neighbors():
    # Block is a still life — each cell has exactly 2-3 neighbors
    g = alive((5, 5), (5, 6), (6, 5), (6, 6))
    result = g.step()
    assert result.is_alive(5, 5)
    assert result.is_alive(5, 6)
    assert result.is_alive(6, 5)
    assert result.is_alive(6, 6)


def test_survival_3_neighbors():
    # Top-left cell of a block has exactly 3 alive neighbors and survives
    g = alive((5, 5), (5, 6), (6, 5), (6, 6))
    result = g.step()
    assert result.is_alive(5, 5)  # 3 neighbors: (5,6), (6,5), (6,6)


# ---------------------------------------------------------------------------
# Conway rules: overpopulation
# ---------------------------------------------------------------------------


def test_overpopulation_4_neighbors_dies():
    # Cell at (1,1) surrounded by 4 live neighbors — dies
    g = alive((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
    result = g.step()
    assert not result.is_alive(1, 1)


# ---------------------------------------------------------------------------
# Conway rules: reproduction
# ---------------------------------------------------------------------------


def test_birth_3_neighbors():
    # Dead cell at (1,1) with exactly 3 alive neighbors
    g = alive((0, 1), (1, 0), (2, 1))
    result = g.step()
    assert result.is_alive(1, 1)


# ---------------------------------------------------------------------------
# Oscillator: blinker (period 2)
# ---------------------------------------------------------------------------


def test_blinker_horizontal_becomes_vertical():
    g = alive((5, 4), (5, 5), (5, 6))
    result = g.step()
    assert result.is_alive(4, 5)
    assert result.is_alive(5, 5)
    assert result.is_alive(6, 5)
    assert not result.is_alive(5, 4)
    assert not result.is_alive(5, 6)


def test_blinker_vertical_becomes_horizontal():
    g = alive((4, 5), (5, 5), (6, 5))
    result = g.step()
    assert result.is_alive(5, 4)
    assert result.is_alive(5, 5)
    assert result.is_alive(5, 6)
    assert not result.is_alive(4, 5)
    assert not result.is_alive(6, 5)


# ---------------------------------------------------------------------------
# Still life: block
# ---------------------------------------------------------------------------


def test_block_is_still_life():
    g = alive((5, 5), (5, 6), (6, 5), (6, 6))
    result = g.step()
    assert result.count() == 4
    assert result.is_alive(5, 5)
    assert result.is_alive(5, 6)
    assert result.is_alive(6, 5)
    assert result.is_alive(6, 6)


# ---------------------------------------------------------------------------
# Glider translation
# ---------------------------------------------------------------------------


def test_glider_moves():
    # Classic glider; after 4 steps it shifts (+1 row, +1 col)
    g = Grid(rows=20, cols=20, alive=[
        (1, 2),
        (2, 3),
        (3, 1), (3, 2), (3, 3),
    ])
    g = g.step()
    g = g.step()
    g = g.step()
    result = g.step()
    assert set(result.alive_cells()) == {(2, 3), (3, 4), (4, 2), (4, 3), (4, 4)}


# ---------------------------------------------------------------------------
# Boundary: non-wrapping
# ---------------------------------------------------------------------------


def test_no_wrap_top_edge():
    # Horizontal blinker on row 0: top neighbors don't exist, so behavior differs.
    # Result is two cells — no wrapping to row -1.
    g = Grid(rows=10, cols=10, alive=[(0, 4), (0, 5), (0, 6)])
    result = g.step()
    assert set(result.alive_cells()) == {(0, 5), (1, 5)}


def test_no_wrap_right_edge():
    # Vertical blinker on col 9: right neighbor col 10 doesn't exist.
    # Result is two cells — no wrapping to col 10.
    g = Grid(rows=10, cols=10, alive=[(4, 9), (5, 9), (6, 9)])
    result = g.step()
    assert set(result.alive_cells()) == {(5, 8), (5, 9)}


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_step_immutable():
    g = alive((5, 5), (5, 6), (5, 7))
    original_cells = set(g.alive_cells())
    _ = g.step()
    assert set(g.alive_cells()) == original_cells


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------


def test_from_dict_round_trip():
    g = alive((1, 1), (2, 3), (5, 5))
    d = g.to_dict()
    g2 = Grid.from_dict(d)
    assert g2.rows == g.rows
    assert g2.cols == g.cols
    assert g2.generation == g.generation
    assert set(g2.alive_cells()) == set(g.alive_cells())


def test_from_dict_handles_lists():
    # JSON gives lists-of-lists, not tuples
    d = {"rows": 20, "cols": 20, "generation": 0, "cells": [[1, 2], [3, 4]]}
    g = Grid.from_dict(d)
    assert g.is_alive(1, 2)
    assert g.is_alive(3, 4)


# ---------------------------------------------------------------------------
# Generation counter
# ---------------------------------------------------------------------------


def test_generation_increments():
    g = Grid()
    assert g.generation == 0
    g2 = g.step()
    assert g2.generation == 1
    g3 = g2.step()
    assert g3.generation == 2


# ---------------------------------------------------------------------------
# Resize
# ---------------------------------------------------------------------------


def test_resize_clips_cells():
    g = Grid(rows=10, cols=10, alive=[(9, 9), (0, 0)])
    result = g.resize(5, 5)
    assert result.rows == 5
    assert result.cols == 5
    assert not result.is_alive(9, 9)
    assert result.is_alive(0, 0)


# ---------------------------------------------------------------------------
# in_bounds
# ---------------------------------------------------------------------------


def test_in_bounds():
    g = Grid(rows=10, cols=10)
    assert g.in_bounds(0, 0)
    assert g.in_bounds(9, 9)
    assert not g.in_bounds(-1, 0)
    assert not g.in_bounds(10, 0)
    assert not g.in_bounds(0, -1)
    assert not g.in_bounds(0, 10)
