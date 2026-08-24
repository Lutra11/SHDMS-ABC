"""Learning-rate-adaptive CMA-ES implementation.

This optimizer follows the repository's bounded CMA-ES implementation and adds
separate learning-rate multipliers for the mean and covariance updates. The
rates are adapted from recent update signal-to-noise proxies, providing a
compact LR-CMA-ES style comparator for experiments.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


class LRCMAESOptimizer:
    """CMA-ES with adaptive mean and covariance learning-rate factors."""

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
        chi_n = math.sqrt(n) * (1.0 - 1.0 / (4.0 * n) + 1.0 / (21.0 * n * n))

        cc = (4.0 + mueff / n) / (n + 4.0 + 2.0 * mueff / n)
        cs = (mueff + 2.0) / (n + mueff + 5.0)
        c1_base = 2.0 / ((n + 1.3) ** 2 + mueff)
        cmu_base = min(1.0 - c1_base, 2.0 * (mueff - 2.0 + 1.0 / mueff) / ((n + 2.0) ** 2 + mueff))
        damps = 1.0 + 2.0 * max(0.0, math.sqrt((mueff - 1.0) / (n + 1.0)) - 1.0) + cs
        eta_m = 1.0
        eta_c = 1.0
        mean_updates: deque[Vector] = deque(maxlen=6)
        cov_updates: deque[Vector] = deque(maxlen=6)

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
            weighted_step = np.sum((arx_internal[order[:mu]] - old_mean) * weights[:, None], axis=0)
            mean = old_mean + eta_m * weighted_step
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
            cov_delta = (
                c1_base * (np.outer(pc, pc) + (1.0 - hsig) * cc * (2.0 - cc) * covariance)
                + cmu_base * rank_mu
                - (c1_base + cmu_base) * covariance
            )
            covariance = covariance + eta_c * cov_delta
            covariance = 0.5 * (covariance + covariance.T)
            covariance += np.eye(n) * 1e-12
            sigma *= math.exp((cs / damps) * (norm_ps / chi_n - 1.0))
            sigma = float(np.clip(sigma, 1e-8, 2.0))

            mean_updates.append(weighted_step.copy())
            cov_updates.append(cov_delta.reshape(-1).copy())
            eta_m = self._adapt_rate(mean_updates, eta_m)
            eta_c = self._adapt_rate(cov_updates, eta_c)

            if generation % max(1, n // 2) == 0:
                eigenvalues, b_matrix = np.linalg.eigh(covariance)
                eigenvalues = np.maximum(eigenvalues, 1e-20)
                d_vector = np.sqrt(eigenvalues)
            history.append(best_value)

        return AlgorithmResult(best.tolist(), best_value, history, self.evaluations)

    def _adapt_rate(self, updates: deque[Vector], current: float) -> float:
        if len(updates) < 3:
            return current
        arr = np.asarray(updates, dtype=float)
        mean_update = np.mean(arr, axis=0)
        signal = float(np.dot(mean_update, mean_update))
        noise = float(np.mean(np.sum((arr - mean_update) ** 2, axis=1))) + 1e-12
        snr = signal / noise
        target = 0.65 + 1.35 * (snr / (1.0 + snr))
        return float(np.clip(0.80 * current + 0.20 * target, 0.35, 2.0))

    def _decode(self, internal: Vector) -> Vector:
        return np.clip(internal, self.lower, self.upper)

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))
