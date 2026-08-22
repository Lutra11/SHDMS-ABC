"""Differential Evolution (DE) implementation used in the experiments."""

from __future__ import annotations

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class DEOptimizer:
    def __init__(self, objective: ObjectiveFunction, bounds: Bounds, config: GenericConfig) -> None:
        self.objective = objective
        self.bounds = np.asarray(bounds, dtype=float)
        self.lower = self.bounds[:, 0]
        self.upper = self.bounds[:, 1]
        self.span = self.upper - self.lower
        self.dimension = len(bounds)
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.evaluations = 0

    def optimize(self) -> AlgorithmResult:
        population = self.lower + self.rng.random((self.config.population, self.dimension)) * self.span
        values = np.array([self._evaluate(x) for x in population], dtype=float)
        best_index = int(np.argmin(values))
        best = population[best_index].copy()
        best_value = float(values[best_index])
        history = [best_value]

        for _ in range(self.config.max_cycles):
            for i in range(self.config.population):
                indices = [idx for idx in range(self.config.population) if idx != i]
                r1, r2, r3 = self.rng.choice(indices, size=3, replace=False)
                donor = population[r1] + 0.5 * (population[r2] - population[r3])
                donor = np.clip(donor, self.lower, self.upper)
                mask = self.rng.random(self.dimension) < 0.9
                mask[int(self.rng.integers(0, self.dimension))] = True
                trial = np.where(mask, donor, population[i])
                value = self._evaluate(trial)
                if value < values[i]:
                    population[i] = trial
                    values[i] = value
                    if value < best_value:
                        best_value = float(value)
                        best = trial.copy()
            history.append(best_value)

        return AlgorithmResult(
            best_position=best.tolist(),
            best_value=best_value,
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
