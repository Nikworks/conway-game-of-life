from __future__ import annotations

from typing import Iterable


class Grid:
    """Conway's Game of Life grid using sparse cell representation.

    Alive cells are stored as a frozenset of (row, col) tuples.
    The grid has finite non-wrapping boundaries.
    step() is immutable — returns a new Grid without mutating self.
    """

    def __init__(
        self,
        rows: int = 60,
        cols: int = 80,
        alive: Iterable[tuple[int, int]] | None = None,
        generation: int = 0,
    ) -> None:
        self.rows = rows
        self.cols = cols
        self.generation = generation
        self._alive: frozenset[tuple[int, int]] = frozenset(alive or [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def alive_cells(self) -> list[tuple[int, int]]:
        """Return list of alive (row, col) tuples, sorted for determinism."""
        return sorted(self._alive)

    def is_alive(self, row: int, col: int) -> bool:
        return (row, col) in self._alive

    def count(self) -> int:
        return len(self._alive)

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    # ------------------------------------------------------------------
    # Mutation helpers (return new Grid)
    # ------------------------------------------------------------------

    def set_cell(self, row: int, col: int, alive: bool) -> Grid:
        if not self.in_bounds(row, col):
            return self
        cells = set(self._alive)
        if alive:
            cells.add((row, col))
        else:
            cells.discard((row, col))
        return Grid(self.rows, self.cols, cells, self.generation)

    def toggle_cell(self, row: int, col: int) -> Grid:
        return self.set_cell(row, col, not self.is_alive(row, col))

    def set_cells(self, cells: Iterable[tuple[int, int]], alive: bool) -> Grid:
        new_alive = set(self._alive)
        for row, col in cells:
            if self.in_bounds(row, col):
                if alive:
                    new_alive.add((row, col))
                else:
                    new_alive.discard((row, col))
        return Grid(self.rows, self.cols, new_alive, self.generation)

    def clear(self) -> Grid:
        return Grid(self.rows, self.cols, generation=self.generation)

    def resize(self, rows: int, cols: int) -> Grid:
        # Clip alive cells to new bounds
        new_alive = {(r, c) for r, c in self._alive if r < rows and c < cols}
        return Grid(rows, cols, new_alive, self.generation)

    # ------------------------------------------------------------------
    # Core game logic
    # ------------------------------------------------------------------

    def step(self) -> Grid:
        """Return a new Grid representing the next generation.

        Uses candidate-based neighbor counting:
        1. For each alive cell, consider it and its 8 neighbors as candidates.
        2. Count how many alive neighbors each candidate has.
        3. Apply Conway rules.
        """
        neighbor_counts: dict[tuple[int, int], int] = {}

        for row, col in self._alive:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = row + dr, col + dc
                    if self.in_bounds(nr, nc):
                        neighbor_counts[(nr, nc)] = neighbor_counts.get((nr, nc), 0) + 1

        next_alive: set[tuple[int, int]] = set()
        # Check all candidates
        candidates = set(neighbor_counts.keys()) | self._alive
        for cell in candidates:
            n = neighbor_counts.get(cell, 0)
            if cell in self._alive:
                # Survival: 2 or 3 neighbors
                if n in (2, 3):
                    next_alive.add(cell)
            else:
                # Birth: exactly 3 neighbors
                if n == 3:
                    if self.in_bounds(*cell):
                        next_alive.add(cell)

        return Grid(self.rows, self.cols, next_alive, self.generation + 1)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "rows": self.rows,
            "cols": self.cols,
            "generation": self.generation,
            "cells": [[r, c] for r, c in self.alive_cells()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Grid:
        cells = [tuple(cell) for cell in data.get("cells", [])]
        return cls(
            rows=data.get("rows", 60),
            cols=data.get("cols", 80),
            alive=cells,
            generation=data.get("generation", 0),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grid):
            return NotImplemented
        return (
            self.rows == other.rows
            and self.cols == other.cols
            and self._alive == other._alive
        )

    def __repr__(self) -> str:
        return (
            f"Grid(rows={self.rows}, cols={self.cols}, "
            f"alive={self.count()}, gen={self.generation})"
        )
