"""CMA-ES implementation used in the experiments."""

from __future__ import annotations

import math

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class CMAESOptimizer:
    """Basic covariance matrix adaptation evolution strategy for bounded problems."""

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
        n = self.dimension
        lam = max(4, int(self.config.population))
        mu = max(2, lam // 2)
        weights = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1))
        weights = weights / np.sum(weights)
        mueff = float(1.0 / np.sum(weights * weights))

        mean = self.lower + 0.5 * self.span
        sigma = 0.30
        pc = np.zeros(n, dtype=float)
        ps = np.zeros(n, dtype=float)
        covariance = np.eye(n, dtype=float)
        b_matrix = np.eye(n, dtype=float)
        d_vector = np.ones(n, dtype=float)
        inv_sqrt_c = np.eye(n, dtype=float)
        chi_n = math.sqrt(n) * (1.0 - 1.0 / (4.0 * n) + 1.0 / (21.0 * n * n))

        cc = (4.0 + mueff / n) / (n + 4.0 + 2.0 * mueff / n)
        cs = (mueff + 2.0) / (n + mueff + 5.0)
        c1 = 2.0 / ((n + 1.3) ** 2 + mueff)
        cmu = min(1.0 - c1, 2.0 * (mueff - 2.0 + 1.0 / mueff) / ((n + 2.0) ** 2 + mueff))
        damps = 1.0 + 2.0 * max(0.0, math.sqrt((mueff - 1.0) / (n + 1.0)) - 1.0) + cs

        best = mean.copy()
        best_value = self._evaluate(self._decode(mean))
        history = [best_value]

        for generation in range(self.config.max_cycles):
            arz = self.rng.normal(0.0, 1.0, (lam, n))
            ary = arz @ (b_matrix * d_vector).T
            arx_internal = mean + sigma * ary
            arx = np.array([self._decode(x) for x in arx_internal])
            values = np.array([self._evaluate(x) for x in arx], dtype=float)
            order = np.argsort(values)

            if values[order[0]] < best_value:
                best_value = float(values[order[0]])
                best = arx[order[0]].copy()

            old_mean = mean.copy()
            mean = np.sum(arx_internal[order[:mu]] * weights[:, None], axis=0)
            y_w = (mean - old_mean) / max(sigma, 1e-12)
            z_w = np.sum(arz[order[:mu]] * weights[:, None], axis=0)

            ps = (1.0 - cs) * ps + math.sqrt(cs * (2.0 - cs) * mueff) * (b_matrix @ z_w)
            norm_ps = float(np.linalg.norm(ps))
            hsig_limit = (1.4 + 2.0 / (n + 1.0)) * chi_n
            hsig_den = math.sqrt(max(1e-12, 1.0 - (1.0 - cs) ** (2.0 * (generation + 1))))
            hsig = 1.0 if norm_ps / hsig_den < hsig_limit else 0.0
            pc = (1.0 - cc) * pc + hsig * math.sqrt(cc * (2.0 - cc) * mueff) * y_w

            rank_mu = np.zeros((n, n), dtype=float)
            for rank, idx in enumerate(order[:mu]):
                y_i = ary[idx]
                rank_mu += weights[rank] * np.outer(y_i, y_i)
            covariance = (
                (1.0 - c1 - cmu) * covariance
                + c1 * (np.outer(pc, pc) + (1.0 - hsig) * cc * (2.0 - cc) * covariance)
                + cmu * rank_mu
            )
            covariance = 0.5 * (covariance + covariance.T)
            sigma *= math.exp((cs / damps) * (norm_ps / chi_n - 1.0))
            sigma = float(np.clip(sigma, 1e-8, 2.0))

            if generation % max(1, n // 2) == 0:
                eigenvalues, b_matrix = np.linalg.eigh(covariance)
                eigenvalues = np.maximum(eigenvalues, 1e-20)
                d_vector = np.sqrt(eigenvalues)
                inv_sqrt_c = b_matrix @ np.diag(1.0 / d_vector) @ b_matrix.T
            _ = inv_sqrt_c
            history.append(best_value)

        return AlgorithmResult(
            best_position=best.tolist(),
            best_value=best_value,
            convergence_history=history,
            evaluations=self.evaluations,
        )

    def _decode(self, internal: Vector) -> Vector:
        return np.clip(internal, self.lower, self.upper)

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
