"""Slime Mould Algorithm (SMA) implementation used in the experiments."""

from __future__ import annotations

import math

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class SMAOptimizer:
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
            order = np.argsort(values)
            population = population[order]
            values = values[order]
            if values[0] < best_value:
                best_value = float(values[0])
                best = population[0].copy()

            worst_value = float(values[-1])
            best_cycle_value = float(values[0])
            weights = self._weights(values, best_cycle_value, worst_value)
            a = math.atanh(max(1e-8, 1.0 - (cycle + 1) / float(self.config.max_cycles + 1)))
            b = 1.0 - (cycle + 1) / float(self.config.max_cycles + 1)
            new_population = population.copy()

            for i in range(population_size):
                if self.rng.random() < 0.03:
                    candidate = self.lower + self.rng.random(self.dimension) * self.span
                else:
                    probability = math.tanh(abs(float(values[i] - best_value)))
                    r1, r2 = self.rng.choice(population_size, size=2, replace=False)
                    vb = self.rng.uniform(-a, a, self.dimension)
                    vc = self.rng.uniform(-b, b, self.dimension)
                    if self.rng.random() < probability:
                        candidate = best + vb * (weights[i] * population[r1] - population[r2])
                    else:
                        candidate = vc * population[i]
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

    def _weights(self, values: Vector, best_value: float, worst_value: float) -> Vector:
        denominator = best_value - worst_value
        if abs(denominator) < 1e-12:
            return weights
        population_size = len(values)
        weights = np.ones(population_size, dtype=float)
        half = population_size // 2
        for i in range(population_size):
            ratio = math.log10((best_value - values[i]) / denominator + 1.0)
            if i < half:
                weights[i] = 1.0 + self.rng.random() * ratio
            else:
                weights[i] = 1.0 - self.rng.random() * ratio
        return weights

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
