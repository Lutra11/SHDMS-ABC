"""Harris Hawks Optimization (HHO) implementation used in the experiments."""

from __future__ import annotations

import math

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class HHOOptimizer:
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
        best_position = population[best_index].copy()
        best_value = float(values[best_index])
        history = [best_value]

        for cycle in range(self.config.max_cycles):
            rabbit_position = best_position.copy()
            mean_hawk = np.mean(population, axis=0)
            energy_factor = 2.0 * (1.0 - cycle / float(max(1, self.config.max_cycles)))

            for i in range(self.config.population):
                candidate = self._update_hawk(
                    current=population[i],
                    rabbit_position=rabbit_position,
                    mean_hawk=mean_hawk,
                    energy_factor=energy_factor,
                )
                candidate_value = self._evaluate(candidate)
                if candidate_value < values[i]:
                    population[i] = candidate
                    values[i] = candidate_value
                    if candidate_value < best_value:
                        best_value = float(candidate_value)
                        best_position = candidate.copy()

            history.append(best_value)

        return AlgorithmResult(
            best_position=best_position.tolist(),
            best_value=best_value,
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _update_hawk(
        self,
        current: Vector,
        rabbit_position: Vector,
        mean_hawk: Vector,
        energy_factor: float,
    ) -> Vector:
        e0 = 2.0 * self.rng.random() - 1.0
        escaping_energy = energy_factor * e0
        q = self.rng.random()
        r = self.rng.random()

        if abs(escaping_energy) >= 1.0:
            return self._exploration_move(current, rabbit_position, mean_hawk, q)

        jump_strength = 2.0 * (1.0 - self.rng.random())
        if r >= 0.5 and abs(escaping_energy) >= 0.5:
            return self._soft_besiege(current, rabbit_position, escaping_energy, jump_strength)
        if r >= 0.5 and abs(escaping_energy) < 0.5:
            return self._hard_besiege(current, rabbit_position, escaping_energy)
        if r < 0.5 and abs(escaping_energy) >= 0.5:
            base = self._soft_besiege(current, rabbit_position, escaping_energy, jump_strength)
            return self._rapid_dive(base, rabbit_position)
        base = self._hard_besiege_with_mean(current, rabbit_position, mean_hawk, escaping_energy, jump_strength)
        return self._rapid_dive(base, rabbit_position)

    def _exploration_move(
        self,
        current: Vector,
        rabbit_position: Vector,
        mean_hawk: Vector,
        q: float,
    ) -> Vector:
        if q >= 0.5:
            random_hawk = self.lower + self.rng.random(self.dimension) * self.span
            candidate = random_hawk - self.rng.random(self.dimension) * np.abs(
                random_hawk - 2.0 * self.rng.random(self.dimension) * current
            )
            return np.clip(candidate, self.lower, self.upper)

        random_site = self.lower + self.rng.random(self.dimension) * self.span
        candidate = rabbit_position - mean_hawk - self.rng.random(self.dimension) * np.abs(random_site - current)
        return np.clip(candidate, self.lower, self.upper)

    def _soft_besiege(
        self,
        current: Vector,
        rabbit_position: Vector,
        escaping_energy: float,
        jump_strength: float,
    ) -> Vector:
        candidate = rabbit_position - escaping_energy * np.abs(jump_strength * rabbit_position - current)
        return np.clip(candidate, self.lower, self.upper)

    def _hard_besiege(
        self,
        current: Vector,
        rabbit_position: Vector,
        escaping_energy: float,
    ) -> Vector:
        candidate = rabbit_position - escaping_energy * np.abs(rabbit_position - current)
        return np.clip(candidate, self.lower, self.upper)

    def _hard_besiege_with_mean(
        self,
        current: Vector,
        rabbit_position: Vector,
        mean_hawk: Vector,
        escaping_energy: float,
        jump_strength: float,
    ) -> Vector:
        candidate = rabbit_position - escaping_energy * np.abs(jump_strength * rabbit_position - mean_hawk)
        return np.clip(candidate, self.lower, self.upper)

    def _rapid_dive(self, base_candidate: Vector, rabbit_position: Vector) -> Vector:
        levy_step = self._levy_flight()
        perturbation = 0.01 * levy_step * self.rng.uniform(-1.0, 1.0, self.dimension) * self.span
        dive = base_candidate + perturbation + 0.005 * (rabbit_position - base_candidate)
        return np.clip(dive, self.lower, self.upper)

    def _levy_flight(self, beta: float = 1.5) -> float:
        sigma = (
            math.gamma(1.0 + beta)
            * math.sin(math.pi * beta / 2.0)
            / (math.gamma((1.0 + beta) / 2.0) * beta * 2.0 ** ((beta - 1.0) / 2.0))
        ) ** (1.0 / beta)
        u = self.rng.normal(0.0, sigma)
        v = self.rng.normal(0.0, 1.0)
        return float(u / (abs(v) ** (1.0 / beta) + 1e-12))

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
