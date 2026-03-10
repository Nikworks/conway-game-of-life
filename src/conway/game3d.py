"""3D cellular automaton grid using sparse cell representation.

Alive cells are stored as a frozenset of (layer, row, col) tuples.
The grid has finite non-wrapping boundaries.
step() is immutable — returns a new Grid3D without mutating self.
"""

from __future__ import annotations

from typing import Iterable


class Grid3D:
    """26-neighbour 3D cellular automaton."""

    def __init__(
        self,
        layers: int = 21,
        rows: int = 21,
        cols: int = 21,
        alive: Iterable[tuple[int, int, int]] | None = None,
        generation: int = 0,
        birth_set: frozenset[int] | None = None,
        survival_set: frozenset[int] | None = None,
    ) -> None:
        self.layers = layers
        self.rows = rows
        self.cols = cols
        self.generation = generation
        # Default B5,6,7 / S5,6,7 (Carter Bays rules)
        self.birth_set: frozenset[int] = birth_set if birth_set is not None else frozenset({5, 6, 7})
        self.survival_set: frozenset[int] = survival_set if survival_set is not None else frozenset({5, 6, 7})
        self._alive: frozenset[tuple[int, int, int]] = frozenset(alive or [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def alive_cells(self) -> list[list[int]]:
        """Return list of [layer, row, col] lists, sorted for determinism."""
        return sorted([list(c) for c in self._alive])

    def is_alive(self, layer: int, row: int, col: int) -> bool:
        return (layer, row, col) in self._alive

    def count(self) -> int:
        return len(self._alive)

    def in_bounds(self, layer: int, row: int, col: int) -> bool:
        return (
            0 <= layer < self.layers
            and 0 <= row < self.rows
            and 0 <= col < self.cols
        )

    # ------------------------------------------------------------------
    # Mutation helpers (return new Grid3D)
    # ------------------------------------------------------------------

    def clear(self) -> Grid3D:
        return Grid3D(
            self.layers, self.rows, self.cols,
            generation=self.generation,
            birth_set=self.birth_set,
            survival_set=self.survival_set,
        )

    # ------------------------------------------------------------------
    # Core game logic
    # ------------------------------------------------------------------

    def step(self) -> Grid3D:
        """Return a new Grid3D representing the next generation.

        Uses candidate-based 26-neighbour counting:
        1. For each alive cell, consider it and its 26 neighbours as candidates.
        2. Count how many alive neighbours each candidate has.
        3. Apply birth_set / survival_set rules.
        """
        neighbor_counts: dict[tuple[int, int, int], int] = {}

        for layer, row, col in self._alive:
            for dl in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dl == 0 and dr == 0 and dc == 0:
                            continue
                        nl, nr, nc = layer + dl, row + dr, col + dc
                        if self.in_bounds(nl, nr, nc):
                            neighbor_counts[(nl, nr, nc)] = (
                                neighbor_counts.get((nl, nr, nc), 0) + 1
                            )

        next_alive: set[tuple[int, int, int]] = set()
        candidates = set(neighbor_counts.keys()) | self._alive
        for cell in candidates:
            n = neighbor_counts.get(cell, 0)
            if cell in self._alive:
                if n in self.survival_set:
                    next_alive.add(cell)
            else:
                if n in self.birth_set and self.in_bounds(*cell):
                    next_alive.add(cell)

        return Grid3D(
            self.layers, self.rows, self.cols,
            alive=next_alive,
            generation=self.generation + 1,
            birth_set=self.birth_set,
            survival_set=self.survival_set,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "layers": self.layers,
            "rows": self.rows,
            "cols": self.cols,
            "generation": self.generation,
            "cells": self.alive_cells(),
        }

    def __repr__(self) -> str:
        return (
            f"Grid3D(layers={self.layers}, rows={self.rows}, cols={self.cols}, "
            f"alive={self.count()}, gen={self.generation})"
        )
