# -*- coding: utf-8 -*-
"""Strict RS activation stress test: SN=6, exactly 6,600 evaluations, uniform-random scout.

Fixes over the earlier 4-13 stress experiment:
  1) budget: a hard evaluation cap of exactly 6,600 (the earlier nominal 6,600
     actually consumed 9,406-9,413 evaluations);
  2) w/o RS: the directed scout candidate is replaced by a uniform random
     candidate (same definition as the Table-15 ablation), instead of
     resetting the trial counter without restarting.

Protocol: S1, SN=6, limit=40 unchanged, tuned parameters, seeds 5000-5049,
100,000 paired bootstrap resamples, two-sided exact paired Wilcoxon.

Reported: RS-triggered runs, total restarts, mean restarts per run,
mean/SD of both variants, paired mean difference with 95% CI, Wilcoxon p,
win proportion of the complete algorithm, and relative difference.
"""
from __future__ import annotations

import argparse
import csv
import functools
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
CODE = PROJECT_ROOT / "ABC_Research" / "code"
PUBLIC_OUT = PROJECT_ROOT / "ABC_Research" / "github-content" / "data" / "revision"
sys.path.insert(0, str(CODE / "other_method"))
sys.path.insert(0, str(CODE / "other_method" / "improved_1"))
sys.path.insert(0, str(HERE))

from ablation_stats import (  # noqa: E402
    paired_bootstrap_mean_ci,
    wilcoxon_signed_rank_exact,
)
from improved_1.base_algorithms import _load_shdms_module  # noqa: E402
from improved_1.benchmark_common import (  # noqa: E402
    ScenarioDefinition,
    build_problem_context,
    create_model_for_scenario,
)

SN = 6
LIMIT = 40
EVALUATIONS_PER_RUN = 6_600
DEFAULT_RUNS = 50
DEFAULT_SEED_START = 5_000
BOOTSTRAP_SEED = 20_261_026
BOOTSTRAP_RESAMPLES = 100_000
DEFAULT_MAX_CYCLES = 500  # matches the original stress operating point
m = _load_shdms_module()
Base = m.SHDMSArtificialBeeColony
Cfg = m.SHDMSABCConfig

TUNED = dict(
    alpha=1.35, beta=1.05, history_rate=0.30, elite_ratio=0.25,
    diff_scale=0.78, elite_scale=0.72, local_best_scale=0.58,
    local_peer_scale=0.24, jump_scale=0.60, jump_noise_scale=0.08,
    crossover_rates=(0.88, 0.92, 0.86, 0.72),
    onlooker_bias=(0.92, 1.05, 1.24, 0.82), local_search_period=4,
    local_search_trials=8, seed_jitter_scale=0.04,
)

SCENARIO = ScenarioDefinition("S1", "base", 1.00, [1.0] * 6, {})


class _BudgetExhausted(Exception):
    """Raised internally when the hard evaluation cap is reached."""


class StrictBudgetBase(Base):
    """Hard cap on total objective evaluations at exactly EVALUATIONS_PER_RUN.

    The base loop consumes SN (init) + cycles*(2*SN + refinement + restarts)
    evaluations; with SN=6 that overshoots a nominal 6,600 budget. The cap
    is enforced inside _evaluate: an evaluation request beyond the cap raises
    _BudgetExhausted, which aborts the current phase mid-step. All committed
    state updates are complete by construction (greedy selection commits only
    after a candidate is evaluated and wins; the aborted candidate is simply
    never committed), so the swarm state stays consistent. Optimization ends
    with exactly 6,600 evaluations.
    """

    budget = EVALUATIONS_PER_RUN

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stopped_cycle = -1

    def _evaluate(self, solution):
        if self.evaluations >= self.budget:
            raise _BudgetExhausted()
        return super()._evaluate(solution)

    def optimize(self):
        self.directed_restarts = 0
        self.max_trial_counter_observed = 0
        try:
            super().optimize()
            raise RuntimeError("budget was not exhausted; increase CYCLES_CEILING")
        except _BudgetExhausted:
            self.stopped_cycle = len(self.convergence_history)
        n = len(self.convergence_history)
        self.metrics_history = self.metrics_history[:n]
        self.operator_probability_history = self.operator_probability_history[:n]
        self.operator_credit_history = self.operator_credit_history[:n]
        return m.SHDMSABCResult(
            best_position=self.best_position.tolist(),
            best_value=float(self.best_value),
            convergence_history=self.convergence_history[:],
            operator_probability_history=self.operator_probability_history[:],
            operator_credit_history=self.operator_credit_history[:],
            metrics_history=self.metrics_history[:],
            operator_success_counts=dict(self.operator_success_counts),
            evaluations=self.evaluations,
        )


class CountingBase(StrictBudgetBase):
    """Instrument directed restarts and peak trial counters."""

    def _scout_bee_phase(self, cycle, metrics, cycle_success_counts, cycle_success_gains):
        if self.trial_counters.size:
            self.max_trial_counter_observed = max(
                self.max_trial_counter_observed, int(np.max(self.trial_counters))
            )
        return super()._scout_bee_phase(
            cycle, metrics, cycle_success_counts, cycle_success_gains
        )

    def _directed_restart(self, index, cycle, metrics):
        self.directed_restarts += 1
        return super()._directed_restart(index, cycle, metrics)


class FullUnderStress(CountingBase):
    pass


class RandomScoutUnderStress(CountingBase):
    """w/o RS: uniform random scout candidate replaces the directed scout.

    Restart bookkeeping stays identical (the counter resets and the restart
    happens), only the candidate generator differs."""

    def _directed_restart(self, index, cycle, metrics):
        # count every scout restart, then draw a uniform random candidate
        # instead of the directed one (evaluate happens in _scout_bee_phase)
        self.directed_restarts += 1
        return self.lower + self.rng.random(self.dimension) * self.span


VARIANT_SPECS = (
    ("full", "SHDMS-ABC (complete)", FullUnderStress),
    ("wo_rs", "SHDMS-ABC w/o RS (random scout)", RandomScoutUnderStress),
)
VARIANT_LABELS = {key: label for key, label, _ in VARIANT_SPECS}


def run_one(task, max_cycles=DEFAULT_MAX_CYCLES, sn=SN):
    variant_key, seed = task
    variant_label, optimizer_class = next(
        spec[1:3] for spec in VARIANT_SPECS if spec[0] == variant_key
    )
    context = build_problem_context()
    model = create_model_for_scenario(context, SCENARIO)
    started = time.perf_counter()
    optimizer = optimizer_class(
        objective=model.objective,
        bounds=model.bounds(),
        config=Cfg(
            food_number=sn, max_cycles=max_cycles, limit=LIMIT,
            seed=seed, **TUNED,
        ),
    )
    result = optimizer.optimize()
    elapsed = time.perf_counter() - started
    if int(result.evaluations) != EVALUATIONS_PER_RUN:
        raise RuntimeError(
            f"{variant_label}/seed {seed}: expected {EVALUATIONS_PER_RUN} "
            f"evaluations, observed {result.evaluations}"
        )
    return {
        "variant": variant_key,
        "variant_label": variant_label,
        "seed": seed,
        "score": float(result.best_value),
        "evaluations": int(result.evaluations),
        "directed_restarts": int(optimizer.directed_restarts),
        "max_trial_counter": int(optimizer.max_trial_counter_observed),
        "stopped_cycle": int(optimizer.stopped_cycle),
        "runtime_s": round(elapsed, 2),
    }


def summarize(records, bootstrap_resamples, max_cycles=DEFAULT_MAX_CYCLES, sn=SN):
    grouped = defaultdict(list)
    for row in records:
        grouped[row["variant"]].append(dict(row))
    for rows in grouped.values():
        rows.sort(key=lambda r: int(r["seed"]))
    seeds = [int(r["seed"]) for r in grouped["full"]]
    full = np.asarray([float(r["score"]) for r in grouped["full"]])
    wo = np.asarray([float(r["score"]) for r in grouped["wo_rs"]])
    full_restarts = np.asarray([int(r["directed_restarts"]) for r in grouped["full"]])
    wo_restarts = np.asarray([int(r["directed_restarts"]) for r in grouped["wo_rs"]])
    triggered = full_restarts > 0
    triggered_wo = wo_restarts > 0

    test = wilcoxon_signed_rank_exact(wo, full)
    ci = paired_bootstrap_mean_ci(
        wo, full, n_resamples=bootstrap_resamples, seed=BOOTSTRAP_SEED
    )
    mean_diff = float(np.mean(wo - full))
    wins = int(np.sum(wo > full))
    losses = int(np.sum(wo < full))
    ties = int(np.sum(wo == full))
    triggered_indices = np.where(triggered)[0]
    triggered_wins = int(np.sum(wo[triggered] > full[triggered]))
    triggered_ties = int(np.sum(wo[triggered] == full[triggered]))

    return {
        "schema_version": 1,
        "protocol": {
            "dataset": "NST-HSR",
            "scenario": "S1 (base)",
            "population": sn,
            "limit": LIMIT,
            "cycles_setting": max_cycles,
            "evaluations_per_run": EVALUATIONS_PER_RUN,
            "runs_per_variant": len(seeds),
            "seeds": [min(seeds), max(seeds)],
            "bootstrap_resamples": bootstrap_resamples,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "difference_definition": "w/o RS minus complete; positive favors complete",
            "wilcoxon": "two-sided exact sign-permutation signed-rank test",
            "rs_ablation": "uniform random scout replaces the directed scout candidate",
        },
        "variants": {
            key: {
                "label": VARIANT_LABELS[key],
                "best_observed": float(np.min(
                    [float(r["score"]) for r in grouped[key]]
                )),
                "mean": float(np.mean([float(r["score"]) for r in grouped[key]])),
                "sample_sd": float(np.std(
                    [float(r["score"]) for r in grouped[key]], ddof=1
                )),
                "restart_triggered_runs": int(np.sum(
                    [int(r["directed_restarts"]) > 0 for r in grouped[key]]
                )),
                "directed_restarts_total": int(sum(
                    int(r["directed_restarts"]) for r in grouped[key]
                )),
                "mean_restarts_per_run": float(np.mean(
                    [int(r["directed_restarts"]) for r in grouped[key]]
                )),
                "max_trial_counter_range": [
                    int(min(int(r["max_trial_counter"]) for r in grouped[key])),
                    int(max(int(r["max_trial_counter"]) for r in grouped[key])),
                ],
            }
            for key in VARIANT_LABELS
        },
        "comparison": {
            "mean_difference_wo_rs_minus_complete": mean_diff,
            "relative_difference_percent": mean_diff / float(np.mean(full)) * 100.0,
            "bootstrap_95_ci": [float(ci[0]), float(ci[1])],
            "wilcoxon_raw_p": test.p_value,
            "wilcoxon_nonzero_pairs": test.nonzero_pairs,
            "degenerate_all_zero": test.degenerate_all_zero,
            "complete_wins": wins,
            "complete_losses": losses,
            "ties": ties,
            "complete_win_proportion_all_runs": wins / len(seeds),
            "triggered_runs_full": int(np.sum(triggered)),
            "triggered_runs_wo_rs": int(np.sum(triggered_wo)),
            "complete_wins_among_triggered": int(triggered_wins),
            "ties_among_triggered": int(triggered_ties),
            "triggered_indices_seeds": [
                int(seeds[i]) for i in triggered_indices
            ],
            "triggered_subset_mean_difference": (
                float(np.mean(wo[triggered] - full[triggered]))
                if np.any(triggered) else None
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--seed-start", type=int, default=DEFAULT_SEED_START)
    parser.add_argument("--bootstrap-resamples", type=int, default=BOOTSTRAP_RESAMPLES)
    parser.add_argument("--output-dir", type=Path, default=HERE / "output")
    parser.add_argument("--no-public-mirror", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    parser.add_argument("--sn", type=int, default=SN)
    parser.add_argument("--tag", type=str, default="")
    args = parser.parse_args()
    seeds = list(range(args.seed_start, args.seed_start + args.runs))
    tasks = [(key, seed) for key, _, _ in VARIANT_SPECS for seed in seeds]
    started = time.perf_counter()
    records = []
    if args.workers <= 1:
        for index, task in enumerate(tasks, start=1):
            record = run_one(task, max_cycles=args.max_cycles, sn=args.sn)
            records.append(record)
            print(
                f"[{index}/{len(tasks)}] {record['variant_label']} seed "
                f"{record['seed']} score={record['score']:.4f} "
                f"restarts={record['directed_restarts']} "
                f"evals={record['evaluations']} cycle={record['stopped_cycle']} "
                f"({record['runtime_s']}s, total {time.perf_counter() - started:.0f}s)",
                flush=True,
            )
    else:
        from multiprocessing import Pool

        with Pool(processes=args.workers) as pool:
            for index, record in enumerate(
                pool.imap_unordered(
                    functools.partial(run_one, max_cycles=args.max_cycles, sn=args.sn),
                    tasks, chunksize=1,
                ), start=1,
            ):
                records.append(record)
                if index % 10 == 0 or index == len(tasks):
                    print(
                        f"[{index}/{len(tasks)}] {record['variant_label']} seed "
                        f"{record['seed']} score={record['score']:.4f} "
                        f"restarts={record['directed_restarts']} "
                        f"(total {time.perf_counter() - started:.0f}s)",
                        flush=True,
                    )
    records.sort(key=lambda r: (r["variant"], int(r["seed"])))
    summary = summarize(
        records, args.bootstrap_resamples, max_cycles=args.max_cycles, sn=args.sn
    )
    suffix = f"_{args.tag}" if args.tag else ""
    stem = f"rs_stress_strict{suffix}"
    destinations = [args.output_dir]
    if not args.no_public_mirror:
        destinations.append(PUBLIC_OUT)
    for directory in destinations:
        directory.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "variant", "variant_label", "seed", "score", "evaluations",
            "directed_restarts", "max_trial_counter", "stopped_cycle", "runtime_s",
        ]
        with (directory / f"{stem}_raw.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
        (directory / f"{stem}_raw.json").write_text(
            json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (directory / f"{stem}_statistics.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print(f"saved {len(records)} records to: {', '.join(map(str, destinations))}")
    print(f"completed in {time.perf_counter() - started:.1f}s")


if __name__ == "__main__":
    main()
