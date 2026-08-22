"""Success-History Driven Dynamic Multi-Strategy Artificial Bee Colony (SHDMS-ABC)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector


@dataclass
class SHDMSABCConfig:
    food_number: int = 30
    max_cycles: int = 300
    limit: int = 50
    seed: Optional[int] = None
    alpha: float = 1.2
    beta: float = 1.0
    history_rate: float = 0.25
    credit_floor: float = 0.05
    elite_ratio: float = 0.2
    improvement_reference: float = 1e-3
    improvement_tolerance: float = 1e-12
    stagnation_threshold: int = 20
    diversity_low_threshold: float = 0.08
    diversity_high_threshold: float = 0.22
    diff_scale: float = 0.85
    elite_scale: float = 0.65
    local_best_scale: float = 0.45
    local_peer_scale: float = 0.18
    jump_scale: float = 0.75
    jump_noise_scale: float = 0.12
    crossover_rates: Tuple[float, float, float, float] = (0.85, 0.90, 0.80, 0.75)
    onlooker_bias: Tuple[float, float, float, float] = (1.0, 1.05, 1.10, 0.95)
    local_search_period: int = 5
    local_search_trials: int = 6
    seed_jitter_scale: float = 0.06


@dataclass
class CycleMetrics:
    diversity: float
    concentration: float
    improvement_rate: float
    stagnation_ratio: float


@dataclass
class SHDMSABCResult:
    best_position: List[float]
    best_value: float
    convergence_history: List[float]
    operator_probability_history: List[List[float]]
    operator_credit_history: List[List[float]]
    metrics_history: List[CycleMetrics]
    operator_success_counts: Dict[str, int]
    evaluations: int


class SHDMSArtificialBeeColony:
    """
    Success-History Driven Dynamic Multi-Strategy Artificial Bee Colony.

    The algorithm maintains a portfolio of four search operators:
    1. Differential exploration operator.
    2. Elite-guided differential operator.
    3. Local exploitation operator.
    4. Long-jump diversification operator.

    Operator selection probabilities are updated by success-history credits and
    population-state weights.
    """

    operator_names = (
        "differential_exploration",
        "elite_guided_differential",
        "local_exploitation",
        "long_jump_diversification",
    )

    def __init__(
        self,
        objective: ObjectiveFunction,
        bounds: Bounds,
        config: Optional[SHDMSABCConfig] = None,
        seed_solutions: Optional[Sequence[Sequence[float]]] = None,
    ) -> None:
        if not bounds:
            raise ValueError("bounds must not be empty")

        self.objective = objective
        self.bounds = np.asarray(bounds, dtype=float)
        self.lower = self.bounds[:, 0]
        self.upper = self.bounds[:, 1]
        self.span = self.upper - self.lower
        self.dimension = len(bounds)
        self.config = config or SHDMSABCConfig()
        self.rng = np.random.default_rng(self.config.seed)
        self.seed_solutions = list(seed_solutions or [])

        if self.config.food_number < 4:
            raise ValueError("food_number must be at least 4")
        if self.config.max_cycles <= 0:
            raise ValueError("max_cycles must be positive")
        if self.config.limit <= 0:
            raise ValueError("limit must be positive")
        if not 0.0 < self.config.elite_ratio <= 1.0:
            raise ValueError("elite_ratio must be in (0, 1]")
        if len(self.config.crossover_rates) != 4:
            raise ValueError("crossover_rates must contain four values")
        if len(self.config.onlooker_bias) != 4:
            raise ValueError("onlooker_bias must contain four values")

        self.food_sources = np.empty((0, 0), dtype=float)
        self.values = np.empty(0, dtype=float)
        self.fitness = np.empty(0, dtype=float)
        self.trial_counters = np.empty(0, dtype=int)
        self.credits = np.ones(4, dtype=float)
        self.evaluations = 0
        self.best_position = np.empty(0, dtype=float)
        self.best_value = math.inf
        self.last_improvement_rate = 0.0
        self.stagnation_cycles = 0
        self.convergence_history: List[float] = []
        self.operator_probability_history: List[List[float]] = []
        self.operator_credit_history: List[List[float]] = []
        self.metrics_history: List[CycleMetrics] = []
        self.operator_success_counts: Dict[str, int] = {
            name: 0 for name in self.operator_names
        }

    def optimize(self) -> SHDMSABCResult:
        self._initialize()

        for cycle in range(self.config.max_cycles):
            metrics = self._compute_cycle_metrics()
            base_probabilities = self._operator_probabilities(metrics)
            self.metrics_history.append(metrics)
            self.operator_probability_history.append(base_probabilities.tolist())
            self.operator_credit_history.append(self.credits.tolist())

            cycle_success_counts = np.zeros(4, dtype=int)
            cycle_success_gains = np.zeros(4, dtype=float)
            previous_best = self.best_value

            self._employed_bee_phase(
                cycle=cycle,
                metrics=metrics,
                base_probabilities=base_probabilities,
                cycle_success_counts=cycle_success_counts,
                cycle_success_gains=cycle_success_gains,
            )
            self._onlooker_bee_phase(
                cycle=cycle,
                metrics=metrics,
                base_probabilities=base_probabilities,
                cycle_success_counts=cycle_success_counts,
                cycle_success_gains=cycle_success_gains,
            )
            self._scout_bee_phase(
                cycle=cycle,
                metrics=metrics,
                cycle_success_counts=cycle_success_counts,
                cycle_success_gains=cycle_success_gains,
            )
            self._best_local_refinement(cycle)

            self._update_success_history(cycle_success_counts, cycle_success_gains)
            self._update_progress(previous_best)
            self.convergence_history.append(self.best_value)

        return SHDMSABCResult(
            best_position=self.best_position.tolist(),
            best_value=float(self.best_value),
            convergence_history=self.convergence_history[:],
            operator_probability_history=self.operator_probability_history[:],
            operator_credit_history=self.operator_credit_history[:],
            metrics_history=self.metrics_history[:],
            operator_success_counts=dict(self.operator_success_counts),
            evaluations=self.evaluations,
        )

    def _initialize(self) -> None:
        self.food_sources = self.lower + self.rng.random(
            (self.config.food_number, self.dimension)
        ) * self.span
        seed_bank = self._build_seed_bank()
        for index, seed in enumerate(seed_bank[: self.config.food_number]):
            self.food_sources[index] = seed
        self.values = np.empty(self.config.food_number, dtype=float)
        self.fitness = np.empty(self.config.food_number, dtype=float)
        self.trial_counters = np.zeros(self.config.food_number, dtype=int)
        self.credits = np.ones(4, dtype=float)
        self.evaluations = 0
        self.best_value = math.inf
        self.best_position = np.empty(self.dimension, dtype=float)
        self.last_improvement_rate = 0.0
        self.stagnation_cycles = 0
        self.convergence_history = []
        self.operator_probability_history = []
        self.operator_credit_history = []
        self.metrics_history = []
        self.operator_success_counts = {name: 0 for name in self.operator_names}

        for index in range(self.config.food_number):
            value = self._evaluate(self.food_sources[index])
            self.values[index] = value
            self.fitness[index] = self._calculate_fitness(value)
            self._update_best(self.food_sources[index], value)

        self.convergence_history.append(self.best_value)

    def _build_seed_bank(self) -> List[Vector]:
        bank: List[Vector] = []
        for raw in self.seed_solutions:
            candidate = np.asarray(raw, dtype=float)
            if candidate.shape != (self.dimension,):
                continue
            clipped = np.clip(candidate, self.lower, self.upper)
            self._append_seed(bank, clipped)
            for scale in (self.config.seed_jitter_scale, self.config.seed_jitter_scale * 1.6):
                jitter = clipped + self.rng.normal(0.0, scale, self.dimension) * self.span
                self._append_seed(bank, np.clip(jitter, self.lower, self.upper))
        return bank

    def _append_seed(self, bank: List[Vector], candidate: Vector) -> None:
        for existing in bank:
            if np.allclose(existing, candidate, atol=1e-10, rtol=0.0):
                return
        bank.append(candidate.copy())

    def _employed_bee_phase(
        self,
        cycle: int,
        metrics: CycleMetrics,
        base_probabilities: Vector,
        cycle_success_counts: Vector,
        cycle_success_gains: Vector,
    ) -> None:
        for index in range(self.config.food_number):
            operator_index = self._sample_operator(base_probabilities)
            candidate = self._generate_candidate(index, operator_index, cycle, metrics)
            self._greedy_selection(
                index,
                candidate,
                operator_index,
                cycle_success_counts,
                cycle_success_gains,
            )

    def _onlooker_bee_phase(
        self,
        cycle: int,
        metrics: CycleMetrics,
        base_probabilities: Vector,
        cycle_success_counts: Vector,
        cycle_success_gains: Vector,
    ) -> None:
        source_probabilities = self._selection_probabilities()
        operator_probabilities = self._phase_operator_probabilities(base_probabilities)

        selected = 0
        while selected < self.config.food_number:
            index = int(self.rng.choice(self.config.food_number, p=source_probabilities))
            operator_index = self._sample_operator(operator_probabilities)
            candidate = self._generate_candidate(index, operator_index, cycle, metrics)
            self._greedy_selection(
                index,
                candidate,
                operator_index,
                cycle_success_counts,
                cycle_success_gains,
            )
            selected += 1

    def _scout_bee_phase(
        self,
        cycle: int,
        metrics: CycleMetrics,
        cycle_success_counts: Vector,
        cycle_success_gains: Vector,
    ) -> None:
        exhausted = np.where(self.trial_counters >= self.config.limit)[0]
        for index in exhausted:
            old_value = self.values[index]
            candidate = self._directed_restart(index, cycle, metrics)
            candidate_value = self._evaluate(candidate)

            self.food_sources[index] = candidate
            self.values[index] = candidate_value
            self.fitness[index] = self._calculate_fitness(candidate_value)
            self.trial_counters[index] = 0
            self._update_best(candidate, candidate_value)

            improvement = self._normalized_improvement(old_value, candidate_value)
            if improvement > 0.0:
                cycle_success_counts[3] += 1
                cycle_success_gains[3] += improvement
                self.operator_success_counts[self.operator_names[3]] += 1

    def _generate_candidate(
        self,
        index: int,
        operator_index: int,
        cycle: int,
        metrics: CycleMetrics,
    ) -> Vector:
        donor = self._apply_operator(index, operator_index, cycle, metrics)
        crossover_rate = self.config.crossover_rates[operator_index]
        trial = self._binomial_crossover(self.food_sources[index], donor, crossover_rate)
        return np.clip(trial, self.lower, self.upper)

    def _apply_operator(
        self,
        index: int,
        operator_index: int,
        cycle: int,
        metrics: CycleMetrics,
    ) -> Vector:
        current = self.food_sources[index]
        r1, r2, r3 = self._pick_distinct_indices(index, 3)
        x_r1 = self.food_sources[r1]
        x_r2 = self.food_sources[r2]
        x_r3 = self.food_sources[r3]
        x_best = self.best_position
        x_elite = self._select_elite_source(exclude=index)

        progress = (cycle + 1) / max(self.config.max_cycles, 1)
        concentration = metrics.concentration
        stagnation = metrics.stagnation_ratio
        improvement = min(
            1.0,
            metrics.improvement_rate / max(self.config.improvement_reference, 1e-12),
        )

        if operator_index == 0:
            scale = self.config.diff_scale * (
                1.15 - 0.35 * progress + 0.40 * stagnation
            )
            donor = current + scale * (x_r1 - x_r2)
        elif operator_index == 1:
            elite_scale = self.config.elite_scale * (0.85 + 0.30 * improvement)
            diff_scale = 0.5 * self.config.diff_scale * (1.00 + 0.20 * concentration)
            donor = current + elite_scale * (x_elite - current) + diff_scale * (
                x_r1 - x_r2
            )
        elif operator_index == 2:
            best_scale = self.config.local_best_scale * (0.60 + 0.90 * concentration)
            peer_scale = self.config.local_peer_scale * (0.50 + 0.50 * improvement)
            donor = current + best_scale * (x_best - current) + peer_scale * (
                current - x_r1
            )
        else:
            jump_scale = self.config.jump_scale * (0.70 + 0.80 * stagnation)
            noise_scale = self.config.jump_noise_scale * (1.00 + 0.50 * stagnation)
            noise = self.rng.uniform(-1.0, 1.0, self.dimension)
            donor = x_best + jump_scale * (x_r2 - x_r3) + noise_scale * self.span * noise

        return donor

    def _greedy_selection(
        self,
        index: int,
        candidate: Vector,
        operator_index: int,
        cycle_success_counts: Vector,
        cycle_success_gains: Vector,
    ) -> None:
        candidate_value = self._evaluate(candidate)
        current_value = self.values[index]

        if candidate_value < current_value:
            improvement = self._normalized_improvement(current_value, candidate_value)
            self.food_sources[index] = candidate
            self.values[index] = candidate_value
            self.fitness[index] = self._calculate_fitness(candidate_value)
            self.trial_counters[index] = 0
            self._update_best(candidate, candidate_value)

            cycle_success_counts[operator_index] += 1
            cycle_success_gains[operator_index] += improvement
            self.operator_success_counts[self.operator_names[operator_index]] += 1
        else:
            self.trial_counters[index] += 1

    def _directed_restart(self, index: int, cycle: int, metrics: CycleMetrics) -> Vector:
        current = self.food_sources[index]
        r1, r2 = self._pick_distinct_indices(index, 2)
        progress = (cycle + 1) / max(self.config.max_cycles, 1)
        stagnation = metrics.stagnation_ratio
        eta = 0.35 + 0.25 * (1.0 - progress)
        lam = self.config.jump_scale * (0.90 + 0.70 * stagnation)
        noise = self.rng.uniform(-1.0, 1.0, self.dimension)
        candidate = (
            0.5 * current
            + 0.5 * self.best_position
            + eta * (self.food_sources[r1] - self.food_sources[r2])
            + lam * self.span * noise
        )
        return np.clip(candidate, self.lower, self.upper)

    def _best_local_refinement(self, cycle: int) -> None:
        progress = (cycle + 1) / max(self.config.max_cycles, 1)
        if progress < 0.20 and (cycle + 1) % self.config.local_search_period != 0:
            return

        best_index = int(np.argmin(self.values))
        best = self.food_sources[best_index].copy()
        best_value = float(self.values[best_index])
        elite = self._select_elite_source(exclude=best_index)
        base_step = self.span * (0.030 * (1.0 - progress) + 0.006)

        for _ in range(self.config.local_search_trials):
            direction = 0.30 * (self.best_position - best) + 0.20 * (elite - best)
            noise = self.rng.normal(0.0, 1.0, self.dimension) * base_step
            candidate = best + direction + noise
            candidate = np.clip(candidate, self.lower, self.upper)
            value = self._evaluate(candidate)
            if value < best_value:
                best = candidate
                best_value = value
                self.food_sources[best_index] = candidate
                self.values[best_index] = value
                self.fitness[best_index] = self._calculate_fitness(value)
                self.trial_counters[best_index] = 0
                self._update_best(candidate, value)

    def _update_success_history(
        self,
        cycle_success_counts: Vector,
        cycle_success_gains: Vector,
    ) -> None:
        eps = 1e-12
        rho = self.config.history_rate

        for operator_index in range(4):
            if cycle_success_counts[operator_index] > 0:
                target = cycle_success_gains[operator_index] / (
                    cycle_success_counts[operator_index] + eps
                )
            else:
                target = self.config.credit_floor

            updated = (1.0 - rho) * self.credits[operator_index] + rho * target
            self.credits[operator_index] = max(self.config.credit_floor, updated)

    def _compute_cycle_metrics(self) -> CycleMetrics:
        center = np.mean(self.food_sources, axis=0)
        norm_span = np.linalg.norm(self.span) + 1e-12
        diversity = float(
            np.mean(np.linalg.norm(self.food_sources - center, axis=1) / norm_span)
        )

        low = self.config.diversity_low_threshold
        high = self.config.diversity_high_threshold
        concentration = float(np.clip((high - diversity) / max(high - low, 1e-12), 0.0, 1.0))
        stagnation_ratio = float(
            np.clip(
                self.stagnation_cycles / max(self.config.stagnation_threshold, 1),
                0.0,
                1.0,
            )
        )

        return CycleMetrics(
            diversity=diversity,
            concentration=concentration,
            improvement_rate=self.last_improvement_rate,
            stagnation_ratio=stagnation_ratio,
        )

    def _operator_probabilities(self, metrics: CycleMetrics) -> Vector:
        p = min(
            1.0,
            metrics.improvement_rate / max(self.config.improvement_reference, 1e-12),
        )
        c = metrics.concentration
        s = metrics.stagnation_ratio

        weights = np.array(
            [
                1.0 + 0.70 * c + 0.90 * s + 0.40 * (1.0 - p),
                1.0 + 0.60 * p + 0.25 * (1.0 - s) + 0.20 * (1.0 - c),
                1.0 + 0.85 * c + 0.55 * p + 0.20 * (1.0 - s),
                1.0 + 0.55 * c + 1.05 * s + 0.45 * (1.0 - p),
            ],
            dtype=float,
        )

        scores = np.power(self.credits + 1e-12, self.config.alpha) * np.power(
            weights + 1e-12,
            self.config.beta,
        )
        return scores / np.sum(scores)

    def _phase_operator_probabilities(self, base_probabilities: Vector) -> Vector:
        bias = np.asarray(self.config.onlooker_bias, dtype=float)
        scores = base_probabilities * bias
        return scores / np.sum(scores)

    def _selection_probabilities(self) -> Vector:
        total_fitness = float(np.sum(self.fitness))
        if total_fitness <= 0.0:
            return np.full(self.config.food_number, 1.0 / self.config.food_number)
        return self.fitness / total_fitness

    def _sample_operator(self, probabilities: Vector) -> int:
        return int(self.rng.choice(4, p=probabilities))

    def _select_elite_source(self, exclude: int) -> Vector:
        elite_count = max(1, int(math.ceil(self.config.food_number * self.config.elite_ratio)))
        ranking = np.argsort(self.values)
        elite_indices = [idx for idx in ranking[:elite_count] if idx != exclude]
        if not elite_indices:
            elite_indices = [idx for idx in ranking if idx != exclude]
        elite_index = int(self.rng.choice(elite_indices))
        return self.food_sources[elite_index]

    def _pick_distinct_indices(self, exclude: int, count: int) -> Tuple[int, ...]:
        candidates = [idx for idx in range(self.config.food_number) if idx != exclude]
        picked = self.rng.choice(candidates, size=count, replace=False)
        return tuple(int(value) for value in picked)

    def _binomial_crossover(
        self,
        current: Vector,
        donor: Vector,
        crossover_rate: float,
    ) -> Vector:
        mask = self.rng.random(self.dimension) < crossover_rate
        forced_index = int(self.rng.integers(0, self.dimension))
        mask[forced_index] = True
        return np.where(mask, donor, current)

    def _update_best(self, candidate: Vector, value: float) -> None:
        if value < self.best_value:
            self.best_value = float(value)
            self.best_position = candidate.copy()

    def _update_progress(self, previous_best: float) -> None:
        improvement = max(0.0, previous_best - self.best_value)
        self.last_improvement_rate = improvement / max(abs(previous_best), 1e-12)

        if improvement > self.config.improvement_tolerance:
            self.stagnation_cycles = 0
        else:
            self.stagnation_cycles += 1

    def _evaluate(self, solution: Vector) -> float:
        self.evaluations += 1
        return float(self.objective(solution.tolist()))

    def _normalized_improvement(self, old_value: float, new_value: float) -> float:
        if new_value >= old_value:
            return 0.0
        return (old_value - new_value) / max(abs(old_value), 1e-12)

    @staticmethod
    def _calculate_fitness(value: float) -> float:
        if value >= 0.0:
            return 1.0 / (1.0 + value)
        return 1.0 + abs(value)


def run_shdms_abc(
    objective: ObjectiveFunction,
    bounds: Bounds,
    config: GenericConfig,
    seed_solutions: Optional[Sequence[Sequence[float]]] = None,
) -> AlgorithmResult:
    shdms_config = SHDMSABCConfig(
        food_number=config.population,
        max_cycles=config.max_cycles,
        limit=config.limit,
        seed=config.seed,
        alpha=1.35,
        beta=1.05,
        history_rate=0.30,
        elite_ratio=0.25,
        diff_scale=0.78,
        elite_scale=0.72,
        local_best_scale=0.58,
        local_peer_scale=0.24,
        jump_scale=0.60,
        jump_noise_scale=0.08,
        crossover_rates=(0.88, 0.92, 0.86, 0.72),
        onlooker_bias=(0.92, 1.05, 1.24, 0.82),
        local_search_period=4,
        local_search_trials=8,
        seed_jitter_scale=0.04,
    )
    optimizer = SHDMSArtificialBeeColony(
        objective=objective,
        bounds=bounds,
        config=shdms_config,
        seed_solutions=seed_solutions,
    )
    result = optimizer.optimize()
    return AlgorithmResult(
        best_position=result.best_position,
        best_value=result.best_value,
        convergence_history=result.convergence_history,
        evaluations=result.evaluations,
    )
