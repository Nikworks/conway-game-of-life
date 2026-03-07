"""Preset patterns for Conway's Game of Life.

Each pattern is a list of (row, col) offsets from (0, 0).
Use center_pattern() to shift a pattern to the center of the grid.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Pattern data
# ---------------------------------------------------------------------------

PATTERNS: dict[str, list[tuple[int, int]]] = {
    "glider": [
        (0, 1),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
    ],
    "blinker": [
        (0, 0),
        (0, 1),
        (0, 2),
    ],
    "toad": [
        (0, 1),
        (0, 2),
        (0, 3),
        (1, 0),
        (1, 1),
        (1, 2),
    ],
    "beacon": [
        (0, 0),
        (0, 1),
        (1, 0),
        (2, 3),
        (3, 2),
        (3, 3),
    ],
    "pulsar": [
        # Period-3 oscillator
        (0, 2), (0, 3), (0, 4), (0, 8), (0, 9), (0, 10),
        (2, 0), (2, 5), (2, 7), (2, 12),
        (3, 0), (3, 5), (3, 7), (3, 12),
        (4, 0), (4, 5), (4, 7), (4, 12),
        (5, 2), (5, 3), (5, 4), (5, 8), (5, 9), (5, 10),
        (7, 2), (7, 3), (7, 4), (7, 8), (7, 9), (7, 10),
        (8, 0), (8, 5), (8, 7), (8, 12),
        (9, 0), (9, 5), (9, 7), (9, 12),
        (10, 0), (10, 5), (10, 7), (10, 12),
        (12, 2), (12, 3), (12, 4), (12, 8), (12, 9), (12, 10),
    ],
    "pentadecathlon": [
        # Period-15 oscillator
        (0, 1),
        (1, 1),
        (2, 0), (2, 2),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 0), (7, 2),
        (8, 1),
        (9, 1),
    ],
    "gosper_glider_gun": [
        # Emits a new glider every 30 generations
        (0, 24),
        (1, 22), (1, 24),
        (2, 12), (2, 13), (2, 20), (2, 21), (2, 34), (2, 35),
        (3, 11), (3, 15), (3, 20), (3, 21), (3, 34), (3, 35),
        (4, 0), (4, 1), (4, 10), (4, 16), (4, 20), (4, 21),
        (5, 0), (5, 1), (5, 10), (5, 14), (5, 16), (5, 17), (5, 22), (5, 24),
        (6, 10), (6, 16), (6, 24),
        (7, 11), (7, 15),
        (8, 12), (8, 13),
    ],
    "r_pentomino": [
        # Chaotic — runs for 1103 generations
        (0, 1), (0, 2),
        (1, 0), (1, 1),
        (2, 1),
    ],
    "diehard": [
        # Dies after 130 generations
        (0, 6),
        (1, 0), (1, 1),
        (2, 1), (2, 5), (2, 6), (2, 7),
    ],
    "acorn": [
        # Takes 5206 generations to stabilize
        (0, 1),
        (1, 3),
        (2, 0), (2, 1), (2, 4), (2, 5), (2, 6),
    ],
    "herschel": [
        # 7-cell methuselah; stabilizes at generation 128
        (0, 1),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 2),
        (3, 0),
    ],
    "t_pentomino": [
        # 5-cell methuselah; runs for hundreds of generations
        (0, 0), (0, 1), (0, 2),
        (1, 1),
        (2, 1),
    ],
    "brain": [
        # Found by David Bell, May 1992
        (0, 1), (0, 2), (0, 3), (0, 13), (0, 14), (0, 15),
        (1, 0), (1, 2), (1, 4), (1, 5), (1, 11), (1, 12), (1, 14), (1, 16),
        (2, 0), (2, 2), (2, 4), (2, 12), (2, 14), (2, 16),
        (3, 1), (3, 3), (3, 4), (3, 6), (3, 7), (3, 9), (3, 10), (3, 12), (3, 13), (3, 15),
        (4, 5), (4, 7), (4, 9), (4, 11),
        (5, 3), (5, 5), (5, 7), (5, 9), (5, 11), (5, 13),
        (6, 2), (6, 3), (6, 5), (6, 7), (6, 9), (6, 11), (6, 13), (6, 14),
        (7, 2), (7, 3), (7, 4), (7, 7), (7, 9), (7, 12), (7, 13), (7, 14),
        (8, 2), (8, 3), (8, 6), (8, 10), (8, 13), (8, 14),
        (9, 1), (9, 6), (9, 7), (9, 9), (9, 10), (9, 15),
        (10, 1), (10, 15),
    ],
}

PRESET_NAMES: list[str] = list(PATTERNS.keys())


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def pattern_bounds(pattern: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    """Return (min_row, min_col, max_row, max_col) for a pattern."""
    if not pattern:
        return (0, 0, 0, 0)
    rows = [r for r, _ in pattern]
    cols = [c for _, c in pattern]
    return (min(rows), min(cols), max(rows), max(cols))


def center_pattern(
    pattern: list[tuple[int, int]],
    grid_rows: int,
    grid_cols: int,
) -> list[tuple[int, int]]:
    """Shift pattern so it is centered in the grid.

    Clips any cells that fall outside grid bounds.
    """
    if not pattern:
        return []

    min_r, min_c, max_r, max_c = pattern_bounds(pattern)
    pat_height = max_r - min_r + 1
    pat_width = max_c - min_c + 1

    offset_r = (grid_rows - pat_height) // 2 - min_r
    offset_c = (grid_cols - pat_width) // 2 - min_c

    result = []
    for r, c in pattern:
        nr, nc = r + offset_r, c + offset_c
        if 0 <= nr < grid_rows and 0 <= nc < grid_cols:
            result.append((nr, nc))
    return result


def get_pattern(name: str) -> list[tuple[int, int]]:
    """Return raw pattern by name, or raise ValueError."""
    if name not in PATTERNS:
        raise ValueError(f"Unknown preset: {name!r}. Available: {PRESET_NAMES}")
    return PATTERNS[name]
