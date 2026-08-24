"""QGDECC-inspired dynamic cooperative co-evolutionary differential evolution.

The implementation is adapted to the common optimizer interface in this
repository. It represents the main reported QGDECC concepts: dynamic variable
decomposition, cooperative subspace evolution, parameter adaptation, and an
increment mutation term that uses searched evolution information.
"""

from __future__ import annotations

from typing import List

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class QGDECCOptimizer:
    """Dynamic hybrid cooperative co-evolutionary DE comparator."""

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
        population_size = max(8, int(self.config.population))
        population = self.lower + self.rng.random((population_size, self.dimension)) * self.span
        values = np.array([self._evaluate(x) for x in population], dtype=float)
        previous_population = population.copy()
        best_index = int(np.argmin(values))
        best = population[best_index].copy()
        best_value = float(values[best_index])
        history = [best_value]

        group_count = max(2, min(8, int(np.sqrt(self.dimension)) + 1))
        group_prob = self.rng.random((self.dimension, group_count))
        group_prob = group_prob / np.sum(group_prob, axis=1, keepdims=True)
        groups = self._sample_groups(group_prob)
        memory_f = 0.55
        memory_cr = 0.85

        for cycle in range(self.config.max_cycles):
            if cycle % max(4, self.config.limit // 2) == 0:
                groups = self._sample_groups(group_prob)
            old_best = best.copy()
            order = np.argsort(values)
            success_group_gain = np.zeros(group_count, dtype=float)
            success_group_count = np.zeros(group_count, dtype=float)

            for gid, dims in enumerate(groups):
                if len(dims) == 0:
                    continue
                for i in range(population_size):
                    f = float(np.clip(memory_f + 0.10 * self.rng.standard_cauchy(), 0.10, 1.0))
                    cr = float(np.clip(self.rng.normal(memory_cr, 0.10), 0.0, 1.0))
                    r1, r2, r3 = self._distinct_indices(population_size, exclude={i})
                    increment = population[i] - previous_population[i]
                    donor = population[i].copy()
                    donor[dims] = (
                        population[r1, dims]
                        + f * (population[r2, dims] - population[r3, dims])
                        + 0.35 * f * (best[dims] - population[i, dims])
                        + 0.20 * increment[dims]
                    )
                    donor = np.clip(donor, self.lower, self.upper)
                    trial = population[i].copy()
                    mask = self.rng.random(len(dims)) < cr
                    mask[int(self.rng.integers(0, len(dims)))] = True
                    trial[dims] = np.where(mask, donor[dims], population[i, dims])
                    trial_value = self._evaluate(trial)
                    if trial_value < values[i]:
                        gain = float(values[i] - trial_value)
                        previous_population[i] = population[i].copy()
                        population[i] = trial
                        values[i] = trial_value
                        success_group_gain[gid] += gain
                        success_group_count[gid] += 1.0
                        memory_f = 0.9 * memory_f + 0.1 * f
                        memory_cr = 0.9 * memory_cr + 0.1 * cr
                        if trial_value < best_value:
                            best_value = float(trial_value)
                            best = trial.copy()

            group_prob = self._update_group_probabilities(group_prob, groups, success_group_gain, success_group_count)
            if np.linalg.norm(best - old_best) < 1e-12 and cycle % 5 == 4:
                worst = np.argsort(values)[-max(1, population_size // 5):]
                population[worst] = self.lower + self.rng.random((len(worst), self.dimension)) * self.span
                values[worst] = np.array([self._evaluate(x) for x in population[worst]], dtype=float)
                best_index = int(np.argmin(values))
                if values[best_index] < best_value:
                    best_value = float(values[best_index])
                    best = population[best_index].copy()
            _ = order
            history.append(best_value)

        return AlgorithmResult(best.tolist(), best_value, history, self.evaluations)

    def _sample_groups(self, probabilities: Vector) -> List[np.ndarray]:
        assignments = [int(self.rng.choice(probabilities.shape[1], p=probabilities[d])) for d in range(self.dimension)]
        groups: List[np.ndarray] = []
        for gid in range(probabilities.shape[1]):
            dims = np.array([d for d, g in enumerate(assignments) if g == gid], dtype=int)
            groups.append(dims)
        return groups

    def _update_group_probabilities(self, probabilities: Vector, groups: List[np.ndarray], gains: Vector, counts: Vector) -> Vector:
        quality = gains / np.maximum(counts, 1.0)
        if float(np.sum(quality)) <= 1e-12:
            return 0.98 * probabilities + 0.02 / probabilities.shape[1]
        quality = quality / np.sum(quality)
        updated = probabilities.copy()
        for gid, dims in enumerate(groups):
            if len(dims) > 0:
                updated[dims, gid] = 0.85 * updated[dims, gid] + 0.15 * quality[gid]
        updated = updated / np.sum(updated, axis=1, keepdims=True)
        return updated

    def _distinct_indices(self, population_size: int, exclude: set[int]) -> List[int]:
        candidates = [idx for idx in range(population_size) if idx not in exclude]
        return list(map(int, self.rng.choice(candidates, size=3, replace=False)))

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
