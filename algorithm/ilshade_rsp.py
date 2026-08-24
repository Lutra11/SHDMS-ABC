"""iLSHADE-RSP-inspired differential evolution optimizer.

This implementation follows the experiment framework used in this repository
and captures the main ideas reported for iLSHADE-RSP: L-SHADE style success
memories, rank-based selective pressure, linear population reduction, and
Cauchy perturbation of the target vector before mutation. It is intended as a
paper-inspired, runnable comparator rather than an official authors' release.
"""

from __future__ import annotations

from typing import List

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class ILSHADERSPOptimizer:
    """Improved L-SHADE-RSP with target-vector Cauchy perturbation."""

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
        initial_size = max(8, int(self.config.population))
        min_size = 4
        max_evaluations = initial_size * max(1, self.config.max_cycles + 1)
        population = self.lower + self.rng.random((initial_size, self.dimension)) * self.span
        values = np.array([self._evaluate(x) for x in population], dtype=float)
        archive = np.empty((0, self.dimension), dtype=float)
        memory_size = 8
        memory_f = np.full(memory_size, 0.5, dtype=float)
        memory_cr = np.full(memory_size, 0.5, dtype=float)
        memory_index = 0

        best_index = int(np.argmin(values))
        best = population[best_index].copy()
        best_value = float(values[best_index])
        history = [best_value]

        for cycle in range(self.config.max_cycles):
            current_size = len(population)
            order = np.argsort(values)
            p_count = max(2, int(np.ceil(0.15 * current_size)))
            success_f: List[float] = []
            success_cr: List[float] = []
            improvements: List[float] = []
            progress = (cycle + 1) / float(self.config.max_cycles + 1)
            jump_rate = 0.20 * (1.0 - progress) + 0.03

            for i in range(current_size):
                mem = int(self.rng.integers(0, memory_size))
                f = self._sample_f(memory_f[mem])
                cr = float(np.clip(self.rng.normal(memory_cr[mem], 0.10), 0.0, 1.0))
                pbest_index = self._rank_pressure_choice(order[:p_count], values)
                r1 = self._random_population_index(current_size, exclude={i, pbest_index})
                union = population if len(archive) == 0 else np.vstack([population, archive])
                r2 = self._random_union_index(len(union), exclude={i, pbest_index, r1})

                target = population[i]
                if self.rng.random() < jump_rate:
                    perturb = 0.05 * (1.0 - progress) * self.span * self.rng.standard_cauchy(self.dimension)
                    target = np.clip(target + perturb, self.lower, self.upper)

                donor = target + f * (population[pbest_index] - target) + f * (population[r1] - union[r2])
                donor = np.clip(donor, self.lower, self.upper)
                trial = self._binomial_crossover(population[i], donor, cr)
                trial_value = self._evaluate(trial)

                if trial_value < values[i]:
                    archive = np.vstack([archive, population[i].copy()])
                    improvement = float(values[i] - trial_value)
                    population[i] = trial
                    values[i] = trial_value
                    success_f.append(f)
                    success_cr.append(cr)
                    improvements.append(max(improvement, 0.0))
                    if trial_value < best_value:
                        best_value = float(trial_value)
                        best = trial.copy()

            if success_f:
                weights = np.asarray(improvements, dtype=float)
                weights = weights / max(float(np.sum(weights)), 1e-12)
                sf = np.asarray(success_f, dtype=float)
                scr = np.asarray(success_cr, dtype=float)
                memory_f[memory_index] = float(np.sum(weights * sf * sf) / max(np.sum(weights * sf), 1e-12))
                memory_cr[memory_index] = float(np.sum(weights * scr))
                memory_index = (memory_index + 1) % memory_size

            target_size = self._target_population_size(initial_size, min_size, max_evaluations)
            if len(population) > target_size:
                keep = np.argsort(values)[:target_size]
                population = population[keep]
                values = values[keep]
            archive = self._trim_archive(archive, len(population))
            history.append(best_value)

        return AlgorithmResult(best.tolist(), best_value, history, self.evaluations)

    def _rank_pressure_choice(self, candidates: Vector, values: Vector) -> int:
        ranks = np.arange(len(candidates), 0, -1, dtype=float)
        probs = ranks / np.sum(ranks)
        return int(self.rng.choice(candidates, p=probs))

    def _target_population_size(self, initial_size: int, min_size: int, max_evaluations: int) -> int:
        ratio = min(1.0, self.evaluations / float(max(1, max_evaluations)))
        return max(min_size, int(round(initial_size + ratio * (min_size - initial_size))))

    def _sample_f(self, mean: float) -> float:
        for _ in range(32):
            value = mean + 0.10 * self.rng.standard_cauchy()
            if value > 0.0:
                return float(min(value, 1.0))
        return 0.5

    def _random_population_index(self, population_size: int, exclude: set[int]) -> int:
        candidates = [idx for idx in range(population_size) if idx not in exclude]
        return int(self.rng.choice(candidates))

    def _random_union_index(self, union_size: int, exclude: set[int]) -> int:
        candidates = [idx for idx in range(union_size) if idx not in exclude]
        return int(self.rng.choice(candidates))

    def _binomial_crossover(self, target: Vector, donor: Vector, cr: float) -> Vector:
        mask = self.rng.random(self.dimension) < cr
        mask[int(self.rng.integers(0, self.dimension))] = True
        return np.where(mask, donor, target)

    def _trim_archive(self, archive: Vector, population_size: int) -> Vector:
        if len(archive) <= population_size:
            return archive
        indices = self.rng.choice(len(archive), size=population_size, replace=False)
        return archive[indices]

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
