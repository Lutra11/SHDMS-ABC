"""Modified Artificial Bee Colony (MABC) optimizer."""

from __future__ import annotations

import numpy as np

from .abc import StandardABC
from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class MABC(StandardABC):
    def __init__(self, objective: ObjectiveFunction, bounds: Bounds, config: GenericConfig) -> None:
        super().__init__(objective, bounds, config)
        self.mutation_factor = 0.6
        self.crossover_rate = 0.85
        self.best_weight = 0.4

    def optimize(self) -> AlgorithmResult:
        self._initialize()
        history = [self.best_value]
        for cycle in range(self.config.max_cycles):
            self._employed_phase(cycle)
            self._onlooker_phase(cycle)
            self._scout_phase(cycle)
            history.append(float(self.best_value))
        return AlgorithmResult(
            best_position=self.best_position.tolist(),
            best_value=float(self.best_value),
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _candidate(self, index: int, cycle: int, onlooker: bool) -> Vector:
        if onlooker:
            return self._onlooker_candidate(index)
        return self._employed_candidate(index)

    def _employed_candidate(self, index: int) -> Vector:
        current = self.population[index]
        partner = self.population[self._pick_distinct(index, 1)[0]]
        candidate = current.copy()
        dim = int(self.rng.integers(0, self.dimension))
        phi = self.rng.uniform(-1.0, 1.0)
        psi = self.rng.uniform(0.0, self.best_weight)
        candidate[dim] = (
            current[dim]
            + phi * (current[dim] - partner[dim])
            + psi * (self.best_position[dim] - current[dim])
        )
        return np.clip(candidate, self.lower, self.upper)

    def _onlooker_candidate(self, index: int) -> Vector:
        current = self.population[index]
        r1, r2 = self._pick_distinct(index, 2)
        x1 = self.population[r1]
        x2 = self.population[r2]
        mutant = (
            self.best_position
            + self.mutation_factor * (x1 - x2)
            + self.best_weight * (self.best_position - current)
        )
        mutant = np.clip(mutant, self.lower, self.upper)
        mask = self.rng.random(self.dimension) < self.crossover_rate
        mask[int(self.rng.integers(0, self.dimension))] = True
        trial = np.where(mask, mutant, current)
        return np.clip(trial, self.lower, self.upper)
