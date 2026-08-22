"""Global-best guided Artificial Bee Colony (Gbest-ABC) optimizer."""

from __future__ import annotations

import numpy as np

from .abc import StandardABC
from .common import Vector


class GbestABC(StandardABC):
    def _candidate(self, index: int, cycle: int, onlooker: bool) -> Vector:
        partner = self._pick_distinct(index, 1)[0]
        dim = int(self.rng.integers(0, self.dimension))
        candidate = self.population[index].copy()
        phi = self.rng.uniform(-1.0, 1.0)
        psi = self.rng.uniform(0.0, 1.5 if onlooker else 1.0)
        candidate[dim] = (
            candidate[dim]
            + phi * (candidate[dim] - self.population[partner, dim])
            + psi * (self.best_position[dim] - candidate[dim])
        )
        return np.clip(candidate, self.lower, self.upper)
