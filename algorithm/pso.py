"""Particle Swarm Optimization (PSO) implementation used in the experiments."""

from __future__ import annotations

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class PSOOptimizer:
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
        position = self.lower + self.rng.random((self.config.population, self.dimension)) * self.span
        velocity = self.rng.uniform(-0.1, 0.1, (self.config.population, self.dimension)) * self.span
        values = np.array([self._evaluate(p) for p in position], dtype=float)
        pbest = position.copy()
        pbest_values = values.copy()
        best_index = int(np.argmin(values))
        gbest = position[best_index].copy()
        gbest_value = float(values[best_index])
        history = [gbest_value]

        for cycle in range(self.config.max_cycles):
            w = 0.9 - 0.5 * (cycle / max(self.config.max_cycles - 1, 1))
            r1 = self.rng.random((self.config.population, self.dimension))
            r2 = self.rng.random((self.config.population, self.dimension))
            velocity = (
                w * velocity
                + 2.0 * r1 * (pbest - position)
                + 2.0 * r2 * (gbest[None, :] - position)
            )
            position = np.clip(position + velocity, self.lower, self.upper)
            values = np.array([self._evaluate(p) for p in position], dtype=float)
            improved = values < pbest_values
            pbest[improved] = position[improved]
            pbest_values[improved] = values[improved]
            best_index = int(np.argmin(pbest_values))
            if pbest_values[best_index] < gbest_value:
                gbest_value = float(pbest_values[best_index])
                gbest = pbest[best_index].copy()
            history.append(gbest_value)

        return AlgorithmResult(
            best_position=gbest.tolist(),
            best_value=gbest_value,
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
