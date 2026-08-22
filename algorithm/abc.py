"""Standard Artificial Bee Colony (ABC) optimizer."""

from __future__ import annotations

import math

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class StandardABC:
    def __init__(self, objective: ObjectiveFunction, bounds: Bounds, config: GenericConfig) -> None:
        self.objective = objective
        self.bounds = np.asarray(bounds, dtype=float)
        self.lower = self.bounds[:, 0]
        self.upper = self.bounds[:, 1]
        self.span = self.upper - self.lower
        self.dimension = len(bounds)
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.population = np.empty((0, 0), dtype=float)
        self.values = np.empty(0, dtype=float)
        self.fitness = np.empty(0, dtype=float)
        self.trials = np.empty(0, dtype=int)
        self.best_position = np.empty(0, dtype=float)
        self.best_value = math.inf
        self.evaluations = 0

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

    def _initialize(self) -> None:
        self.population = self.lower + self.rng.random((self.config.population, self.dimension)) * self.span
        self.values = np.empty(self.config.population, dtype=float)
        self.fitness = np.empty(self.config.population, dtype=float)
        self.trials = np.zeros(self.config.population, dtype=int)
        self.best_value = math.inf
        self.best_position = np.empty(self.dimension, dtype=float)
        self.evaluations = 0
        for i in range(self.config.population):
            value = self._evaluate(self.population[i])
            self.values[i] = value
            self.fitness[i] = self._fitness(value)
            self._update_best(self.population[i], value)

    def _employed_phase(self, cycle: int) -> None:
        for i in range(self.config.population):
            candidate = self._candidate(i, cycle, onlooker=False)
            self._greedy_update(i, candidate)

    def _onlooker_phase(self, cycle: int) -> None:
        probabilities = self.fitness / max(np.sum(self.fitness), 1e-12)
        for _ in range(self.config.population):
            i = int(self.rng.choice(self.config.population, p=probabilities))
            candidate = self._candidate(i, cycle, onlooker=True)
            self._greedy_update(i, candidate)

    def _scout_phase(self, cycle: int) -> None:
        exhausted = np.where(self.trials >= self.config.limit)[0]
        for i in exhausted:
            candidate = self.lower + self.rng.random(self.dimension) * self.span
            value = self._evaluate(candidate)
            self.population[i] = candidate
            self.values[i] = value
            self.fitness[i] = self._fitness(value)
            self.trials[i] = 0
            self._update_best(candidate, value)

    def _candidate(self, index: int, cycle: int, onlooker: bool) -> Vector:
        partner = self._pick_distinct(index, 1)[0]
        dim = int(self.rng.integers(0, self.dimension))
        candidate = self.population[index].copy()
        phi = self.rng.uniform(-1.0, 1.0)
        candidate[dim] = candidate[dim] + phi * (candidate[dim] - self.population[partner, dim])
        return np.clip(candidate, self.lower, self.upper)

    def _greedy_update(self, index: int, candidate: Vector) -> None:
        value = self._evaluate(candidate)
        if value < self.values[index]:
            self.population[index] = candidate
            self.values[index] = value
            self.fitness[index] = self._fitness(value)
            self.trials[index] = 0
            self._update_best(candidate, value)
        else:
            self.trials[index] += 1

    def _pick_distinct(self, exclude: int, count: int) -> Tuple[int, ...]:
        indices = [i for i in range(self.config.population) if i != exclude]
        picked = self.rng.choice(indices, size=count, replace=False)
        return tuple(int(v) for v in picked)

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))

    def _update_best(self, candidate: Vector, value: float) -> None:
        if value < self.best_value:
            self.best_value = float(value)
            self.best_position = candidate.copy()

    @staticmethod
    def _fitness(value: float) -> float:
        if value >= 0.0:
            return 1.0 / (1.0 + value)
        return 1.0 + abs(value)
