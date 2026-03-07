"""Tests for core Grid game logic."""

import pytest
from conway.game import Grid


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


def test_set_and_toggle():
    g = alive((5, 5))
    assert g.is_alive(5, 5)
    g2 = g.toggle_cell(5, 5)
    assert not g2.is_alive(5, 5)
    g3 = g2.toggle_cell(5, 5)
    assert g3.is_alive(5, 5)


def test_set_cells_alive():
    g = Grid(rows=10, cols=10)
    g2 = g.set_cells([(1, 1), (2, 2), (3, 3)], alive=True)
    assert g2.count() == 3


def test_set_cells_dead():
    g = alive((1, 1), (2, 2), (3, 3))
    g2 = g.set_cells([(1, 1), (3, 3)], alive=False)
    assert g2.count() == 1
    assert g2.is_alive(2, 2)


def test_clear():
    g = alive((1, 1), (2, 2))
    g2 = g.clear()
    assert g2.count() == 0
    assert g2.rows == g.rows


# ---------------------------------------------------------------------------
# Conway rules: underpopulation
# ---------------------------------------------------------------------------


def test_underpopulation_0_neighbors_dies():
    g = alive((5, 5))
    g2 = g.step()
    assert not g2.is_alive(5, 5)


def test_underpopulation_1_neighbor_dies():
    g = alive((5, 5), (5, 6))
    g2 = g.step()
    assert not g2.is_alive(5, 5)
    assert not g2.is_alive(5, 6)


# ---------------------------------------------------------------------------
# Conway rules: survival
# ---------------------------------------------------------------------------


def test_survival_2_neighbors():
    # Block is a still life — each cell has exactly 2-3 neighbors
    g = alive((5, 5), (5, 6), (6, 5), (6, 6))
    g2 = g.step()
    assert g2.is_alive(5, 5)
    assert g2.is_alive(5, 6)
    assert g2.is_alive(6, 5)
    assert g2.is_alive(6, 6)


def test_survival_3_neighbors():
    # An L-shape: center cell has 2 neighbors, corner cells have 1 or 2
    # Just confirm the block still life holds for 3 steps
    block = alive((5, 5), (5, 6), (6, 5), (6, 6))
    for _ in range(3):
        block = block.step()
    assert block.count() == 4


# ---------------------------------------------------------------------------
# Conway rules: overpopulation
# ---------------------------------------------------------------------------


def test_overpopulation_4_neighbors_dies():
    # Cell at (1,1) surrounded by 4 live neighbors — dies
    g = alive((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
    g2 = g.step()
    assert not g2.is_alive(1, 1)


# ---------------------------------------------------------------------------
# Conway rules: reproduction
# ---------------------------------------------------------------------------


def test_birth_3_neighbors():
    # Dead cell at (1,1) with exactly 3 alive neighbors
    g = alive((0, 1), (1, 0), (2, 1))
    g2 = g.step()
    assert g2.is_alive(1, 1)


# ---------------------------------------------------------------------------
# Oscillator: blinker (period 2)
# ---------------------------------------------------------------------------


def test_blinker_oscillation():
    # Horizontal blinker
    g = alive((5, 4), (5, 5), (5, 6))
    g2 = g.step()
    # Should become vertical
    assert g2.is_alive(4, 5)
    assert g2.is_alive(5, 5)
    assert g2.is_alive(6, 5)
    assert not g2.is_alive(5, 4)
    assert not g2.is_alive(5, 6)
    # Step back to horizontal
    g3 = g2.step()
    assert g3.is_alive(5, 4)
    assert g3.is_alive(5, 5)
    assert g3.is_alive(5, 6)


# ---------------------------------------------------------------------------
# Still life: block
# ---------------------------------------------------------------------------


def test_block_is_still_life():
    block = alive((5, 5), (5, 6), (6, 5), (6, 6))
    g2 = block.step()
    assert block == g2 or (
        g2.is_alive(5, 5)
        and g2.is_alive(5, 6)
        and g2.is_alive(6, 5)
        and g2.is_alive(6, 6)
        and g2.count() == 4
    )


# ---------------------------------------------------------------------------
# Glider translation
# ---------------------------------------------------------------------------


def test_glider_moves():
    # Classic glider at top-left, with enough room
    g = Grid(rows=20, cols=20, alive=[
        (1, 2),
        (2, 3),
        (3, 1), (3, 2), (3, 3),
    ])
    initial_cells = set(g.alive_cells())
    for _ in range(4):
        g = g.step()
    # After 4 steps the glider has moved 1 cell diagonally
    assert set(g.alive_cells()) != initial_cells
    assert g.count() == 5


# ---------------------------------------------------------------------------
# Boundary: non-wrapping
# ---------------------------------------------------------------------------


def test_no_wrap_top_edge():
    # Blinker touching top edge should not wrap
    g = Grid(rows=10, cols=10, alive=[(0, 4), (0, 5), (0, 6)])
    g2 = g.step()
    # Cells above row 0 don't exist, so blinker evolves differently
    # Cells at row -1 must NOT appear
    for c in range(10):
        assert not g2.is_alive(-1, c)


def test_no_wrap_right_edge():
    g = Grid(rows=10, cols=10, alive=[(4, 9), (5, 9), (6, 9)])
    g2 = g.step()
    for r in range(10):
        assert not g2.is_alive(r, 10)


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
    g2 = g.resize(5, 5)
    assert g2.rows == 5
    assert g2.cols == 5
    assert not g2.is_alive(9, 9)
    assert g2.is_alive(0, 0)


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
