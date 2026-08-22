"""RIME optimizer implementation used in the experiments."""

from __future__ import annotations

import math

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class RIMEOptimizer:
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
        population_size = max(4, int(self.config.population))
        population = self.lower + self.rng.random((population_size, self.dimension)) * self.span
        values = np.array([self._evaluate(x) for x in population], dtype=float)
        best_index = int(np.argmin(values))
        best = population[best_index].copy()
        best_value = float(values[best_index])
        history = [best_value]

        for cycle in range(self.config.max_cycles):
            progress = (cycle + 1) / float(self.config.max_cycles + 1)
            normalized = self._normalize(values)
            new_population = population.copy()
            rime_factor = (
                (self.rng.random() - 0.5)
                * 2.0
                * math.cos(math.pi * progress / 2.0)
                * (1.0 - progress)
            )

            for i in range(population_size):
                candidate = population[i].copy()
                for j in range(self.dimension):
                    if self.rng.random() < math.sqrt(progress):
                        candidate[j] = best[j] + rime_factor * (
                            self.lower[j] + self.rng.random() * self.span[j]
                        )
                    if self.rng.random() < normalized[i]:
                        candidate[j] = best[j]
                candidate = np.clip(candidate, self.lower, self.upper)
                candidate_value = self._evaluate(candidate)
                if candidate_value < values[i]:
                    new_population[i] = candidate
                    values[i] = candidate_value
                    if candidate_value < best_value:
                        best_value = float(candidate_value)
                        best = candidate.copy()
            population = new_population
            history.append(best_value)

        return AlgorithmResult(
            best_position=best.tolist(),
            best_value=best_value,
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _normalize(self, values: Vector) -> Vector:
        worst = float(np.max(values))
        best = float(np.min(values))
        if abs(worst - best) < 1e-12:
            return np.ones(len(values), dtype=float)
        scores = (worst - values) / (worst - best)
        return np.clip(scores, 0.0, 1.0)

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
