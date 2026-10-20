# -*- coding: utf-8 -*-
"""R4-C5 equal-evaluation-budget control (public repository implementation).

Part A: SHDMS-ABC truncated to exactly 2,904 objective evaluations per run -
the per-run evaluation count of the single-phase baselines (PSO/DE/GWO/HHO).
Part B: the four single-phase baselines at their native budget under the same
protocol (population 24, seeds 2020-2049, 30 runs per scenario), so the
budget-matched comparison is fully self-contained and reproducible from the
public repository alone.

Per-run scores are stored for every algorithm and scenario, so every mean and
standard deviation reported in the manuscript can be recomputed independently.

Output: data/revision/equal_budget_shdms.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from statistics import mean, pstdev

import numpy as np

from common.paths import GIT_CONTENT_DIR, ensure_import_paths

ensure_import_paths()

from algorithm import GenericConfig, optimize_algorithm  # noqa: E402
from common.model import build_dataset_model, create_scenario_model, benchmark_score  # noqa: E402
from common.runtime import run_algorithm  # noqa: E402

EVAL_CAP = 2904          # single-phase per-run evaluation count (PSO/DE/GWO/HHO)
POP, CYC, LIM = 24, 120, 40
SEED0, RUNS = 2020, 30
SCENARIOS = ("S1", "S2", "S3", "S4")
SINGLE_PHASE = ("PSO", "DE", "GWO", "HHO")
OUT = GIT_CONTENT_DIR / "data" / "revision" / "equal_budget_shdms.json"


class EvalCap:
    """Hard evaluation counter wrapping model.objective; after the cap every
    further call returns +inf. The final plan is evaluated uncapped via
    model.evaluate_vector, so the reported metrics are unaffected."""

    def __init__(self, fn, cap):
        self.fn = fn
        self.cap = cap
        self.n = 0

    def __call__(self, x):
        if self.n >= self.cap:
            return 1e12
        self.n += 1
        return self.fn(x)


def main() -> None:
    results = []
    base = build_dataset_model("NST-HSR")
    for scenario in SCENARIOS:
        model = create_scenario_model(base, scenario)
        t0 = time.time()

        # Part A: SHDMS-ABC truncated to the single-phase budget.
        shdms_runs = []
        for r in range(RUNS):
            cap = EvalCap(model.objective, EVAL_CAP)
            cfg = GenericConfig(population=POP, max_cycles=CYC, limit=LIM,
                                seed=SEED0 + r)
            res = optimize_algorithm("SHDMS-ABC", cap, model.bounds(), cfg)
            ms = model.evaluate_vector(res.best_position)
            shdms_runs.append({
                "run": r + 1, "seed": SEED0 + r, "score": benchmark_score(ms),
                "evals": min(cap.n, EVAL_CAP),
                "departures": int(np.sum(ms.departures)),
                "avg_wait_min": float(ms.average_waiting_time),
                "avg_load_pct": float(ms.average_load * 100),
                "coverage_pct": float(ms.demand_coverage * 100),
                "max_capacity_utilization_pct": float(ms.max_capacity_utilization * 100),
            })
        scores = [r["score"] for r in shdms_runs]
        entry = {
            "scenario": scenario,
            "shdms_truncated": {
                "algorithm": "SHDMS-ABC@%d" % EVAL_CAP, "eval_cap": EVAL_CAP,
                "runs": RUNS, "seed_first": SEED0,
                "score_mean": mean(scores), "score_std": pstdev(scores),
                "per_run": shdms_runs,
            },
            "baselines": {},
        }

        # Part B: single-phase baselines at their native budget.
        for algo in SINGLE_PHASE:
            bl = []
            for r in range(RUNS):
                rec, _, _ = run_algorithm(
                    model, algo, SEED0 + r, POP, EVAL_CAP, LIM,
                    run=r + 1, dataset="NST-HSR", scenario=scenario)
                bl.append({"run": r + 1, "seed": SEED0 + r,
                           "score": rec.score, "evals": rec.evaluations})
            s = [b["score"] for b in bl]
            ev = mean(b["evals"] for b in bl)
            entry["baselines"][algo] = {
                "runs": RUNS, "score_mean": mean(s), "score_std": pstdev(s),
                "evals_mean": ev, "per_run": bl,
            }
            print(f"[{scenario}] {algo:9s}: {mean(s):9.4f}+/-{pstdev(s):7.4f} "
                  f"evals={ev:7.0f}", flush=True)

        results.append(entry)
        st = entry["shdms_truncated"]
        print(f"[{scenario}] SHDMS-ABC@{EVAL_CAP}: {st['score_mean']:9.4f}"
              f"+/-{st['score_std']:7.4f} ({time.time()-t0:.0f}s)", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("saved ->", OUT, flush=True)


if __name__ == "__main__":
    main()
