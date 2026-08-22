"""Memetic Artificial Bee Colony (MeABC) optimizer."""

from __future__ import annotations

import numpy as np

from .abc import StandardABC
from .common import AlgorithmResult


class MeABC(StandardABC):
    def optimize(self) -> AlgorithmResult:
        self._initialize()
        history = [self.best_value]
        for cycle in range(self.config.max_cycles):
            self._employed_phase(cycle)
            self._onlooker_phase(cycle)
            self._memetic_search(cycle)
            self._scout_phase(cycle)
            history.append(float(self.best_value))
        return AlgorithmResult(
            best_position=self.best_position.tolist(),
            best_value=float(self.best_value),
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _memetic_search(self, cycle: int) -> None:
        best_index = int(np.argmin(self.values))
        best = self.population[best_index].copy()
        scale = 0.12 * (1.0 - cycle / max(self.config.max_cycles, 1)) + 0.02
        for _ in range(4):
            candidate = best + self.rng.uniform(-1.0, 1.0, self.dimension) * self.span * scale
            candidate = np.clip(candidate, self.lower, self.upper)
            value = self._evaluate(candidate)
            if value < self.values[best_index]:
                self.population[best_index] = candidate
                self.values[best_index] = value
                self.fitness[best_index] = self._fitness(value)
                self.trials[best_index] = 0
                best = candidate
                self._update_best(candidate, value)
