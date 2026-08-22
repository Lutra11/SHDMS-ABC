"""Improved Artificial Bee Colony (IABC) optimizer."""

from __future__ import annotations

import numpy as np

from .abc import StandardABC
from .common import Vector


class IABC(StandardABC):
    def _candidate(self, index: int, cycle: int, onlooker: bool) -> Vector:
        r1, r2, r3 = self._pick_distinct(index, 3)
        current = self.population[index]
        phi = self.rng.uniform(-1.0, 1.0, self.dimension)
        psi = self.rng.uniform(0.0, 1.0, self.dimension)
        mask = self.rng.random(self.dimension) < (0.45 if onlooker else 0.30)
        if not np.any(mask):
            mask[int(self.rng.integers(0, self.dimension))] = True
        donor = current.copy()
        donor[mask] = (
            current[mask]
            + phi[mask] * (current[mask] - self.population[r1, mask])
            + 0.35 * psi[mask] * (self.population[r2, mask] - self.population[r3, mask])
            + (0.20 if onlooker else 0.10) * psi[mask] * (self.best_position[mask] - current[mask])
        )
        return np.clip(donor, self.lower, self.upper)
