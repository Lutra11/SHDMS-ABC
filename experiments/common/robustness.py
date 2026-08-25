"""Shared one-factor objective-weight and penalty robustness experiments."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

import numpy as np

from .model import ModelParameters, build_dataset_model
from .runtime import run_algorithm


WEIGHTS = {
    "w1": "omega_run_cost", "w2": "omega_wait_cost",
    "w3": "omega_occ_loss", "w4": "omega_stop_cost",
}
PENALTIES = {
    "λ1": "penalty_cap", "λ2": "penalty_load", "λ3": "penalty_revenue",
    "λ4": "penalty_demand", "λ5": "penalty_safe",
}


def normalized_weight_overrides(parameters: ModelParameters, key: str, factor: float) -> Dict[str, float]:
    base = {name: float(getattr(parameters, name)) for name in WEIGHTS.values()}
    changed = base[key] * factor
    remaining_scale = (1.0 - changed) / (1.0 - base[key])
    return {name: (changed if name == key else value * remaining_scale) for name, value in base.items()}


def run_robustness(group: str, runs: int, population: int, target: int, limit: int, seed: int):
    baseline_model = build_dataset_model("NST-HSR")
    parameters = baseline_model.base.parameters
    settings = [("Baseline", "1.00", {})]
    if group == "weight":
        for symbol, key in WEIGHTS.items():
            for factor, level in ((0.75, "-25%"), (1.25, "+25%")):
                settings.append((symbol, level, normalized_weight_overrides(parameters, key, factor)))
    elif group == "penalty":
        for symbol, key in PENALTIES.items():
            for factor, level in ((0.5, "×0.5"), (2.0, "×2.0")):
                settings.append((symbol, level, {key: float(getattr(parameters, key)) * factor}))
    else:
        raise ValueError("group must be either weight or penalty")

    raw: List[Dict[str, object]] = []
    for parameter, level, overrides in settings:
        model = build_dataset_model("NST-HSR", overrides)
        for offset in range(runs):
            record, _, metrics = run_algorithm(model, "SHDMS-ABC", seed + offset, population, target, limit, offset + 1, "NST-HSR", "S1")
            raw.append(record.to_dict() | {
                "parameter": parameter, "level": level,
                "intervals": ";".join(f"{value:.8f}" for value in metrics.intervals),
                "constraint_violation": record.hard_violation + record.soft_violation,
            })

    grouped = defaultdict(list)
    for row in raw:
        grouped[(str(row["parameter"]), str(row["level"]))].append(row)
    baseline = grouped[("Baseline", "1.00")]
    base_intervals = np.mean([np.fromstring(str(row["intervals"]), sep=";") for row in baseline], axis=0)
    base_departures = float(np.mean([float(row["daily_departures"]) for row in baseline]))
    base_wait = float(np.mean([float(row["wait_cost"]) for row in baseline]))
    base_run = float(np.mean([float(row["run_cost"]) for row in baseline]))
    base_time = float(np.mean([float(row["runtime_s"]) for row in baseline]))
    summary = []
    for parameter, level, _ in settings:
        subset = grouped[(parameter, level)]
        intervals = np.mean([np.fromstring(str(row["intervals"]), sep=";") for row in subset], axis=0)
        runtime = float(np.mean([float(row["runtime_s"]) for row in subset]))
        summary.append({
            "Parameter setting": parameter, "Perturbation level": level,
            "MARD_h/%": float(np.mean(np.abs(intervals - base_intervals) / np.maximum(base_intervals, 1e-9)) * 100),
            "Maximum period deviation/min": float(np.max(np.abs(intervals - base_intervals))),
            "Departure change/trains": float(np.mean([float(row["daily_departures"]) for row in subset]) - base_departures),
            "Waiting cost change/%": float((np.mean([float(row["wait_cost"]) for row in subset]) - base_wait) / base_wait * 100),
            "Operating cost change/%": float((np.mean([float(row["run_cost"]) for row in subset]) - base_run) / base_run * 100),
            "Mean constraint violation": float(np.mean([float(row["constraint_violation"]) for row in subset])),
            "Maximum constraint violation": float(np.max([float(row["constraint_violation"]) for row in subset])),
            "Feasible rate/%": 100 * sum(str(row["feasible"]).lower() == "true" for row in subset) / len(subset),
            "Mean runtime/s": runtime,
            "Runtime change/%": (runtime - base_time) / max(base_time, 1e-12) * 100,
        })
    return raw, summary
