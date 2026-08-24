"""Common optimizer runner, run records and SHDMS-ABC ablation variants."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, replace
from typing import Dict, List, Mapping, Sequence

import numpy as np

from .model import ImprovedModel, PlanMetrics, benchmark_score, hard_violation, soft_violation
from .paths import ensure_import_paths

ensure_import_paths()

from algorithm import (  # noqa: E402
    AlgorithmResult, CycleMetrics, GenericConfig, SHDMSABCConfig,
    SHDMSArtificialBeeColony, StandardABC, optimize_algorithm,
)


CORE_ALGORITHMS = [
    "DE", "LSHADE", "iLSHADE-RSP", "QGDECC", "CMA-ES",
    "LR-CMA-ES", "HHO", "RIME", "MIRIME", "SHDMS-ABC",
]
OPERATIONAL_ALGORITHMS = ["ABC", "DE", "GWO", *[a for a in CORE_ALGORITHMS if a != "DE"]]
CROSSLINE_ALGORITHMS = ["ABC", "DE", "LSHADE", "iLSHADE-RSP", "QGDECC", "CMA-ES", "LR-CMA-ES", "RIME", "MIRIME", "SHDMS-ABC"]


@dataclass
class RunRecord:
    dataset: str
    scenario: str
    algorithm: str
    run: int
    seed: int
    score: float
    objective: float
    runtime_s: float
    evaluations: int
    convergence_cycle: int
    feasible: bool
    hard_violation: float
    soft_violation: float
    average_waiting_time: float
    average_load: float
    max_capacity_utilization: float
    daily_departures: int
    run_cost: float
    wait_cost: float
    revenue: float
    best_position: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def cycles_for_budget(algorithm: str, target_evaluations: int, population: int) -> int:
    """Translate a target NFE to cycles using each implementation's evaluation pattern."""
    name = algorithm.upper()
    if name == "SHDMS-ABC":
        return max(1, round((target_evaluations - population) / (2.0 * population + 1.2)))
    if name in {"LSHADE", "L-SHADE"}:
        # The repository's linear population reduction averages about 22
        # evaluations per cycle for the manuscript setting SN=30.
        return max(1, round(target_evaluations / 22.0))
    if name in {"CMA-ES", "CMAES"}:
        return max(1, round((target_evaluations - 1) / population))
    return max(1, round(target_evaluations / population) - 1)


def convergence_cycle(history: Sequence[float], tolerance: float = 0.01) -> int:
    if not history:
        return 0
    final = history[-1]
    threshold = final * (1 + tolerance) if final >= 0 else final * (1 - tolerance)
    return next((index for index, value in enumerate(history) if value <= threshold), len(history) - 1)


def run_algorithm(
    model: ImprovedModel, algorithm: str, seed: int, population: int,
    target_evaluations: int, limit: int = 30, run: int = 1,
    dataset: str = "NST-HSR", scenario: str = "S1", use_seed_solutions: bool = False,
) -> tuple[RunRecord, AlgorithmResult, PlanMetrics]:
    config = GenericConfig(population=population, max_cycles=cycles_for_budget(algorithm, target_evaluations, population), limit=limit, seed=seed)
    start = time.perf_counter()
    result = optimize_algorithm(
        algorithm, model.objective, model.bounds(), config,
        seed_solutions=model.seed_solutions() if use_seed_solutions else None,
    )
    elapsed = time.perf_counter() - start
    metrics = model.evaluate_vector(result.best_position)
    record = RunRecord(
        dataset, scenario, algorithm, run, seed, benchmark_score(metrics), metrics.objective,
        elapsed, result.evaluations, convergence_cycle(result.convergence_history),
        hard_violation(metrics) <= 1e-9, hard_violation(metrics), soft_violation(metrics),
        metrics.average_waiting_time, metrics.average_load, metrics.max_capacity_utilization,
        int(np.sum(metrics.departures)), metrics.run_cost, metrics.wait_cost, metrics.revenue,
        ";".join(f"{value:.10g}" for value in result.best_position),
    )
    return record, result, metrics


def run_repeated(model: ImprovedModel, algorithms: Sequence[str], runs: int, population: int, target_evaluations: int, limit: int, seed: int, dataset: str, scenario: str) -> List[RunRecord]:
    records: List[RunRecord] = []
    for algorithm in algorithms:
        for offset in range(runs):
            # Common random-number seeds make cross-algorithm paired tests valid.
            run_seed = seed + offset
            record, _, _ = run_algorithm(model, algorithm, run_seed, population, target_evaluations, limit, offset + 1, dataset, scenario)
            records.append(record)
    return records


def build_shdms_config(population: int, max_cycles: int, limit: int, seed: int, overrides: Mapping[str, float] | None = None) -> SHDMSABCConfig:
    config = SHDMSABCConfig(
        food_number=population, max_cycles=max_cycles, limit=limit, seed=seed,
        alpha=1.35, beta=1.05, history_rate=0.30, credit_floor=0.05,
        diversity_low_threshold=0.08, diversity_high_threshold=0.22,
        elite_ratio=0.25, diff_scale=0.78, elite_scale=0.72,
        local_best_scale=0.58, local_peer_scale=0.24, jump_scale=0.60,
        jump_noise_scale=0.08, crossover_rates=(0.88, 0.92, 0.86, 0.72),
        onlooker_bias=(0.92, 1.05, 1.24, 0.82), local_search_period=4,
        local_search_trials=8, seed_jitter_scale=0.04,
    )
    values = dict(overrides or {})
    if "diversity_low_threshold" in values and "diversity_high_threshold" not in values:
        values["diversity_high_threshold"] = min(0.35, float(values["diversity_low_threshold"]) + 0.14)
    return replace(config, **values)


class VariantSHDMSABC(SHDMSArtificialBeeColony):
    def __init__(self, *args, variant: str = "SHDMS-ABC", **kwargs):
        super().__init__(*args, **kwargs)
        self.variant = variant

    def _operator_probabilities(self, metrics: CycleMetrics) -> np.ndarray:
        return np.full(4, 0.25) if self.variant == "w/o OW" else super()._operator_probabilities(metrics)

    def _phase_operator_probabilities(self, base_probabilities: np.ndarray) -> np.ndarray:
        return np.full(4, 0.25) if self.variant == "w/o OW" else super()._phase_operator_probabilities(base_probabilities)

    def _update_success_history(self, cycle_success_counts, cycle_success_gains) -> None:
        if self.variant != "w/o SH":
            super()._update_success_history(cycle_success_counts, cycle_success_gains)

    def _compute_cycle_metrics(self) -> CycleMetrics:
        metrics = super()._compute_cycle_metrics()
        return replace(metrics, concentration=0.50) if self.variant == "w/o DT" else metrics

    def _scout_bee_phase(self, cycle, metrics, cycle_success_counts, cycle_success_gains) -> None:
        if self.variant == "w/o RS":
            self.trial_counters[self.trial_counters >= self.config.limit] = 0
        else:
            super()._scout_bee_phase(cycle, metrics, cycle_success_counts, cycle_success_gains)


def run_variant(model: ImprovedModel, variant: str, seed: int, population: int, max_cycles: int, limit: int, overrides: Mapping[str, float] | None = None):
    start = time.perf_counter()
    if variant == "Basic ABC":
        result = StandardABC(model.objective, model.bounds(), GenericConfig(population, max_cycles, limit, seed)).optimize()
    else:
        raw = VariantSHDMSABC(model.objective, model.bounds(), build_shdms_config(population, max_cycles, limit, seed, overrides), seed_solutions=model.seed_solutions(), variant=variant).optimize()
        result = AlgorithmResult(raw.best_position, raw.best_value, raw.convergence_history, raw.evaluations)
    elapsed = time.perf_counter() - start
    metrics = model.evaluate_vector(result.best_position)
    return result, metrics, elapsed
