"""Grey Wolf Optimizer (GWO) implementation used in the experiments."""

from __future__ import annotations

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class GWOOptimizer:
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
        wolves = self.lower + self.rng.random((self.config.population, self.dimension)) * self.span
        values = np.array([self._evaluate(w) for w in wolves], dtype=float)
        history = [float(np.min(values))]

        for cycle in range(self.config.max_cycles):
            order = np.argsort(values)
            alpha = wolves[order[0]].copy()
            beta = wolves[order[1]].copy()
            delta = wolves[order[2]].copy()
            alpha_value = float(values[order[0]])
            a = 2.0 - 2.0 * (cycle / max(self.config.max_cycles - 1, 1))

            for i in range(self.config.population):
                r1 = self.rng.random(self.dimension)
                r2 = self.rng.random(self.dimension)
                A1 = 2.0 * a * r1 - a
                C1 = 2.0 * r2
                D_alpha = np.abs(C1 * alpha - wolves[i])
                X1 = alpha - A1 * D_alpha

                r1 = self.rng.random(self.dimension)
                r2 = self.rng.random(self.dimension)
                A2 = 2.0 * a * r1 - a
                C2 = 2.0 * r2
                D_beta = np.abs(C2 * beta - wolves[i])
                X2 = beta - A2 * D_beta

                r1 = self.rng.random(self.dimension)
                r2 = self.rng.random(self.dimension)
                A3 = 2.0 * a * r1 - a
                C3 = 2.0 * r2
                D_delta = np.abs(C3 * delta - wolves[i])
                X3 = delta - A3 * D_delta

                candidate = np.clip((X1 + X2 + X3) / 3.0, self.lower, self.upper)
                value = self._evaluate(candidate)
                wolves[i] = candidate
                values[i] = value
                if value < alpha_value:
                    alpha_value = value
                    alpha = candidate.copy()
            history.append(alpha_value)

        best_index = int(np.argmin(values))
        return AlgorithmResult(
            best_position=wolves[best_index].tolist(),
            best_value=float(values[best_index]),
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
