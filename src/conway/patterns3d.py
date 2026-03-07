"""Preset patterns for 3D cellular automata.

Each pattern is a list of (layer, row, col) offsets from (0, 0, 0).
Use center_pattern_3d() to shift a pattern to the centre of the grid.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Pattern data
# ---------------------------------------------------------------------------

PATTERNS_3D: dict[str, dict] = {
    "carter_bays_glider": {
        # B6/S5,6,7 — translating object in 3D space
        "birth_set": frozenset({6}),
        "survival_set": frozenset({5, 6, 7}),
        "cells": [
            (0, 1, 0),
            (0, 1, 2),
            (0, 2, 1),
            (1, 0, 1),
            (1, 1, 0),
            (1, 1, 2),
            (1, 2, 1),
        ],
    },
    "accordion": {
        # B4,5/S5 — expands and contracts
        "birth_set": frozenset({4, 5}),
        "survival_set": frozenset({5}),
        "cells": [
            (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1),
            (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1),
        ],
    },
    "bad_reaction": {
        # B4,5/S5 — chaotic growth pattern
        "birth_set": frozenset({4, 5}),
        "survival_set": frozenset({5}),
        "cells": [
            (0, 1, 1),
            (1, 0, 1), (1, 1, 0), (1, 1, 2), (1, 2, 1),
            (2, 1, 1),
        ],
    },
}

PRESET_NAMES_3D: list[str] = list(PATTERNS_3D.keys())


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def pattern_bounds_3d(
    cells: list[tuple[int, int, int]],
) -> tuple[int, int, int, int, int, int]:
    """Return (min_layer, min_row, min_col, max_layer, max_row, max_col)."""
    if not cells:
        return (0, 0, 0, 0, 0, 0)
    ls = [l for l, _, _ in cells]
    rs = [r for _, r, _ in cells]
    cs = [c for _, _, c in cells]
    return (min(ls), min(rs), min(cs), max(ls), max(rs), max(cs))


def center_pattern_3d(
    cells: list[tuple[int, int, int]],
    grid_layers: int,
    grid_rows: int,
    grid_cols: int,
) -> list[tuple[int, int, int]]:
    """Shift pattern to be centred in the grid. Clips out-of-bounds cells."""
    if not cells:
        return []

    min_l, min_r, min_c, max_l, max_r, max_c = pattern_bounds_3d(cells)
    height = max_l - min_l + 1
    depth  = max_r - min_r + 1
    width  = max_c - min_c + 1

    off_l = (grid_layers - height) // 2 - min_l
    off_r = (grid_rows   - depth)  // 2 - min_r
    off_c = (grid_cols   - width)  // 2 - min_c

    result = []
    for l, r, c in cells:
        nl, nr, nc = l + off_l, r + off_r, c + off_c
        if 0 <= nl < grid_layers and 0 <= nr < grid_rows and 0 <= nc < grid_cols:
            result.append((nl, nr, nc))
    return result


def get_pattern_3d(name: str) -> dict:
    """Return pattern dict (birth_set, survival_set, cells) by name, or raise ValueError."""
    if name not in PATTERNS_3D:
        raise ValueError(f"Unknown 3D preset: {name!r}. Available: {PRESET_NAMES_3D}")
    return PATTERNS_3D[name]
