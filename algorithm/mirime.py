"""MIRIME-inspired multi-strategy RIME optimizer.

This file implements a runnable comparator following the MIRIME mechanisms:
Tent chaotic initialization, leader-centroid guidance, lens-imaging opposition
learning, and centroid-based boundary control.
"""

from __future__ import annotations

import math

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class MIRIMEOptimizer:
    """Multi-strategy improved RIME optimizer."""

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
        population = self._tent_population(population_size)
        values = np.array([self._evaluate(x) for x in population], dtype=float)
        best_index = int(np.argmin(values))
        best = population[best_index].copy()
        best_value = float(values[best_index])
        history = [best_value]

        for cycle in range(self.config.max_cycles):
            progress = (cycle + 1) / float(self.config.max_cycles + 1)
            normalized = self._normalize(values)
            centroid = np.mean(population, axis=0)
            new_population = population.copy()
            rime_factor = (
                (self.rng.random() - 0.5)
                * 2.0
                * math.cos(math.pi * progress / 2.0)
                * (1.0 - progress)
            )

            for i in range(population_size):
                candidate = population[i].copy()
                leader_pull = best - population[i]
                centroid_pull = centroid - population[i]
                for j in range(self.dimension):
                    if self.rng.random() < math.sqrt(progress):
                        adaptive_anchor = best[j] + 0.45 * leader_pull[j] + 0.25 * centroid_pull[j]
                        candidate[j] = adaptive_anchor + rime_factor * (
                            self.lower[j] + self.rng.random() * self.span[j]
                        )
                    if self.rng.random() < normalized[i]:
                        candidate[j] = best[j]
                candidate = self._centroid_boundary(candidate, centroid)
                candidate_value = self._evaluate(candidate)
                if candidate_value < values[i]:
                    new_population[i] = candidate
                    values[i] = candidate_value
                    if candidate_value < best_value:
                        best_value = float(candidate_value)
                        best = candidate.copy()
            population = new_population

            if cycle % max(3, self.config.limit // 3) == 0:
                population, values, best, best_value = self._lens_opposition(population, values, best, best_value)
            history.append(best_value)

        return AlgorithmResult(best.tolist(), best_value, history, self.evaluations)

    def _tent_population(self, population_size: int) -> Vector:
        x = self.rng.random((population_size, self.dimension))
        for _ in range(5):
            x = np.where(x < 0.5, 2.0 * x, 2.0 * (1.0 - x))
            x = np.clip(x + 1e-12 * self.rng.random(x.shape), 0.0, 1.0)
        return self.lower + x * self.span

    def _centroid_boundary(self, candidate: Vector, centroid: Vector) -> Vector:
        candidate = candidate.copy()
        low_mask = candidate < self.lower
        high_mask = candidate > self.upper
        candidate[low_mask] = 0.5 * (centroid[low_mask] + self.lower[low_mask])
        candidate[high_mask] = 0.5 * (centroid[high_mask] + self.upper[high_mask])
        return np.clip(candidate, self.lower, self.upper)

    def _lens_opposition(self, population: Vector, values: Vector, best: Vector, best_value: float):
        centroid = np.mean(population, axis=0)
        scale = 1.0 + self.rng.random(self.dimension)
        opposed = centroid + (centroid - population) / scale
        opposed = np.clip(opposed, self.lower, self.upper)
        opposed_values = np.array([self._evaluate(x) for x in opposed], dtype=float)
        improve = opposed_values < values
        population[improve] = opposed[improve]
        values[improve] = opposed_values[improve]
        best_index = int(np.argmin(values))
        if values[best_index] < best_value:
            best_value = float(values[best_index])
            best = population[best_index].copy()
        return population, values, best, best_value

    def _normalize(self, values: Vector) -> Vector:
        worst = float(np.max(values))
        best = float(np.min(values))
        if abs(worst - best) < 1e-12:
            return np.ones(len(values), dtype=float)
        return np.clip((worst - values) / (worst - best), 0.0, 1.0)

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
