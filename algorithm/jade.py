"""JADE adaptive differential evolution implementation used in the experiments."""

from __future__ import annotations

from typing import List

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class JADEOptimizer:
    """JADE with current-to-pbest mutation and an external archive."""

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
        archive = np.empty((0, self.dimension), dtype=float)
        mu_f = 0.5
        mu_cr = 0.5
        c = 0.1
        p = 0.1

        best_index = int(np.argmin(values))
        best = population[best_index].copy()
        best_value = float(values[best_index])
        history = [best_value]

        for _ in range(self.config.max_cycles):
            order = np.argsort(values)
            p_count = max(2, int(np.ceil(p * population_size)))
            success_f: List[float] = []
            success_cr: List[float] = []

            for i in range(population_size):
                f = self._sample_f(mu_f)
                cr = float(np.clip(self.rng.normal(mu_cr, 0.1), 0.0, 1.0))
                pbest_index = int(self.rng.choice(order[:p_count]))
                r1 = self._random_population_index(population_size, exclude={i, pbest_index})
                union = population if len(archive) == 0 else np.vstack([population, archive])
                r2 = self._random_union_index(len(union), exclude={i, pbest_index, r1})

                donor = (
                    population[i]
                    + f * (population[pbest_index] - population[i])
                    + f * (population[r1] - union[r2])
                )
                donor = np.clip(donor, self.lower, self.upper)
                trial = self._binomial_crossover(population[i], donor, cr)
                trial_value = self._evaluate(trial)

                if trial_value < values[i]:
                    archive = np.vstack([archive, population[i].copy()])
                    population[i] = trial
                    values[i] = trial_value
                    success_f.append(f)
                    success_cr.append(cr)
                    if trial_value < best_value:
                        best_value = float(trial_value)
                        best = trial.copy()

            archive = self._trim_archive(archive, population_size)
            if success_f:
                sf = np.asarray(success_f, dtype=float)
                scr = np.asarray(success_cr, dtype=float)
                mu_f = (1.0 - c) * mu_f + c * float(np.sum(sf * sf) / max(np.sum(sf), 1e-12))
                mu_cr = (1.0 - c) * mu_cr + c * float(np.mean(scr))
            history.append(best_value)

        return AlgorithmResult(
            best_position=best.tolist(),
            best_value=best_value,
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _sample_f(self, mu_f: float) -> float:
        for _ in range(32):
            value = mu_f + 0.1 * self.rng.standard_cauchy()
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
