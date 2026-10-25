# -*- coding: utf-8 -*-
"""2x2 factorial ablation of SHDMS-ABC across scenarios S1-S4 (NST-HSR).

Variants (pre-specified):
  full        complete SHDMS-ABC
  no_sh       w/o SH   (success-history credits frozen at 1.0)
  no_ps       w/o PS   (population-state scheduling neutralized)
  no_sh_ps    w/o SH+PS (both disabled jointly)

Protocol: SN=24, 120 cycles, limit=40, tuned parameters, seeds 5000-5049,
exactly 6,600 objective evaluations per run (asserted), 100,000 paired
bootstrap resamples, two-sided exact paired Wilcoxon signed-rank tests,
Holm adjustment over the 12 primary contrasts (3 variants x 4 scenarios),
plus the pre-specified interaction contrast
  I = joint - w/oSH - w/oPS + complete  (per-seed, positive = synergy)
and relative differences dF% = mean(variant-complete)/mean(complete)*100.
"""
from __future__ import annotations

import argparse
import csv
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
    holm_adjust,
    paired_bootstrap_mean_ci,
    wilcoxon_signed_rank_exact,
)
from improved_1.base_algorithms import _load_shdms_module  # noqa: E402
from improved_1.benchmark_common import (  # noqa: E402
    build_problem_context,
    create_model_for_scenario,
    scenario_definitions,
)

POPULATION = 24
CYCLES = 120
LIMIT = 40
EVALUATIONS_PER_RUN = 6_600
DEFAULT_RUNS = 50
DEFAULT_SEED_START = 5_000
BOOTSTRAP_SEED = 20_261_026
BOOTSTRAP_RESAMPLES = 100_000

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


class CountingBase(Base):
    """Instrument directed restarts without changing candidate generation."""

    def _initialize(self):
        self.directed_restarts = 0
        self.max_trial_counter_observed = 0
        return super()._initialize()

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


class CompleteSHDMS(CountingBase):
    pass


class NoSuccessHistory(CountingBase):
    def _update_success_history(self, cycle_success_counts, cycle_success_gains):
        self.credits[:] = 1.0


class NoStateScheduling(CountingBase):
    def _neutral_metrics(self, metrics):
        return m.CycleMetrics(
            diversity=metrics.diversity,
            concentration=0.5,
            improvement_rate=self.config.improvement_reference,
            stagnation_ratio=0.0,
        )

    def _operator_probabilities(self, metrics):
        scores = np.power(self.credits + 1e-12, self.config.alpha)
        return scores / np.sum(scores)

    def _phase_operator_probabilities(self, base_probabilities):
        return base_probabilities / np.sum(base_probabilities)

    def _apply_operator(self, index, operator_index, cycle, metrics):
        return super()._apply_operator(
            index, operator_index, cycle, self._neutral_metrics(metrics)
        )

    def _directed_restart(self, index, cycle, metrics):
        return super()._directed_restart(index, cycle, self._neutral_metrics(metrics))


class NoSuccessHistoryNoStateScheduling(NoSuccessHistory, NoStateScheduling):
    """Joint variant: credits frozen AND state scheduling neutralized.

    Method resolution follows the same overrides as the single-mechanism
    variants; with credits fixed at 1.0 the operator distribution reduces to
    a fixed uniform distribution over the four operators.
    """
    pass


VARIANT_SPECS = (
    ("full", "SHDMS-ABC", CompleteSHDMS, True),
    ("no_sh", "SHDMS-ABC w/o SH", NoSuccessHistory, True),
    ("no_ps", "SHDMS-ABC w/o PS", NoStateScheduling, True),
    ("no_sh_ps", "SHDMS-ABC w/o SH+PS", NoSuccessHistoryNoStateScheduling, True),
)
VARIANT_LABELS = {key: label for key, label, _, _ in VARIANT_SPECS}
COMPARISON_KEYS = ("no_sh", "no_ps", "no_sh_ps")
COMPARISON_NAMES = {
    "no_sh": "w/o SH",
    "no_ps": "w/o PS",
    "no_sh_ps": "w/o SH+PS",
}

SCENARIOS = [s for s in scenario_definitions() if s.code in ("S1", "S2", "S3", "S4")]
SCENARIO_CODES = [s.code for s in SCENARIOS]

_MODELS: dict[str, Any] = {}


def _get_model(scenario_code: str):
    if scenario_code not in _MODELS:
        scenario = next(s for s in SCENARIOS if s.code == scenario_code)
        context = build_problem_context()
        _MODELS[scenario_code] = create_model_for_scenario(context, scenario)
    return _MODELS[scenario_code]


def run_one(task: tuple[str, str, int]) -> dict[str, Any]:
    scenario_code, variant_key, seed = task
    variant_label, optimizer_class = next(
        spec[1:3] for spec in VARIANT_SPECS if spec[0] == variant_key
    )
    model = _get_model(scenario_code)
    started = time.perf_counter()
    optimizer = optimizer_class(
        objective=model.objective,
        bounds=model.bounds(),
        config=Cfg(
            food_number=POPULATION, max_cycles=CYCLES, limit=LIMIT,
            seed=seed, **TUNED,
        ),
    )
    result = optimizer.optimize()
    elapsed = time.perf_counter() - started
    if int(result.evaluations) != EVALUATIONS_PER_RUN:
        raise RuntimeError(
            f"{scenario_code}/{variant_label}/seed {seed}: expected "
            f"{EVALUATIONS_PER_RUN} evaluations, observed {result.evaluations}"
        )
    return {
        "scenario": scenario_code,
        "variant": variant_key,
        "variant_label": variant_label,
        "seed": seed,
        "score": float(result.best_value),
        "evaluations": int(result.evaluations),
        "directed_restarts": int(optimizer.directed_restarts),
        "max_trial_counter": int(optimizer.max_trial_counter_observed),
        "runtime_s": round(elapsed, 2),
    }


def build_tasks(seeds: Sequence[int], scenario_codes: Sequence[str]) -> list[tuple[str, str, int]]:
    return [
        (scenario_code, variant_key, seed)
        for scenario_code in scenario_codes
        for variant_key, _, _, _ in VARIANT_SPECS
        for seed in seeds
    ]


def summarize(records: Sequence[Mapping[str, Any]], bootstrap_resamples: int) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[(row["scenario"], row["variant"])].append(dict(row))
    for rows in grouped.values():
        rows.sort(key=lambda r: int(r["seed"]))
    seeds = sorted(int(r["seed"]) for r in grouped[(SCENARIO_CODES[0], "full")])
    summary: dict[str, Any] = {
        "schema_version": 1,
        "protocol": {
            "dataset": "NST-HSR",
            "scenarios": SCENARIO_CODES,
            "runs_per_variant_per_scenario": len(seeds),
            "seeds": [min(seeds), max(seeds)],
            "population": POPULATION,
            "cycles": CYCLES,
            "limit": LIMIT,
            "evaluations_per_run": EVALUATIONS_PER_RUN,
            "bootstrap_resamples": bootstrap_resamples,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "difference_definition": "variant minus complete; positive favors complete",
            "wilcoxon": "two-sided exact sign-permutation signed-rank test",
            "multiplicity": "Holm adjustment over 12 primary contrasts (3 variants x 4 scenarios)",
            "primary_contrast": "F(w/o SH+PS) - F(complete) per scenario",
            "interaction": "I = F(w/o SH+PS) - F(w/o SH) - F(w/o PS) + F(complete), per seed",
        },
        "scenarios": {},
        "holm_family": {},
    }
    raw_p: dict[str, float] = {}
    for scenario_code in SCENARIO_CODES:
        arrays = {
            key: np.asarray(
                [float(r["score"]) for r in grouped[(scenario_code, key)]], dtype=float
            )
            for key in VARIANT_LABELS
        }
        restart_runs = {
            key: int(sum(r["directed_restarts"] > 0 for r in grouped[(scenario_code, key)]))
            for key in VARIANT_LABELS
        }
        scenario_summary: dict[str, Any] = {"variants": {}, "comparisons": {}, "interaction": {}}
        for key in VARIANT_LABELS:
            values = arrays[key]
            scenario_summary["variants"][key] = {
                "label": VARIANT_LABELS[key],
                "best_observed": float(np.min(values)),
                "mean": float(np.mean(values)),
                "sample_sd": float(np.std(values, ddof=1)),
                "restart_triggered_runs": restart_runs[key],
            }
        for key in COMPARISON_KEYS:
            variant = arrays[key]
            complete = arrays["full"]
            test = wilcoxon_signed_rank_exact(variant, complete)
            ci = paired_bootstrap_mean_ci(
                variant, complete, n_resamples=bootstrap_resamples, seed=BOOTSTRAP_SEED
            )
            contrast_id = f"{scenario_code}:{key}"
            raw_p[contrast_id] = test.p_value
            mean_diff = float(np.mean(variant - complete))
            scenario_summary["comparisons"][key] = {
                "name": COMPARISON_NAMES[key],
                "mean_difference_variant_minus_complete": mean_diff,
                "relative_difference_percent": mean_diff / float(np.mean(complete)) * 100.0,
                "bootstrap_95_ci": [float(ci[0]), float(ci[1])],
                "wilcoxon_raw_p": test.p_value,
                "wilcoxon_nonzero_pairs": test.nonzero_pairs,
                "degenerate_all_zero": test.degenerate_all_zero,
            }
        interaction = (
            arrays["no_sh_ps"] - arrays["no_sh"] - arrays["no_ps"] + arrays["full"]
        )
        interaction_test = wilcoxon_signed_rank_exact(interaction, np.zeros_like(interaction))
        interaction_ci = paired_bootstrap_mean_ci(
            interaction, np.zeros_like(interaction),
            n_resamples=bootstrap_resamples, seed=BOOTSTRAP_SEED,
        )
        scenario_summary["interaction"] = {
            "mean": float(np.mean(interaction)),
            "bootstrap_95_ci": [float(interaction_ci[0]), float(interaction_ci[1])],
            "wilcoxon_raw_p": interaction_test.p_value,
            "wilcoxon_nonzero_pairs": interaction_test.nonzero_pairs,
            "degenerate_all_zero": interaction_test.degenerate_all_zero,
        }
        summary["scenarios"][scenario_code] = scenario_summary
    adjusted = holm_adjust(raw_p)
    for contrast_id, p_value in adjusted.items():
        summary["holm_family"][contrast_id] = {
            "raw_p": raw_p[contrast_id], "holm_adjusted_p": p_value
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--seed-start", type=int, default=DEFAULT_SEED_START)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--scenarios", type=str, default=",".join(SCENARIO_CODES))
    parser.add_argument("--bootstrap-resamples", type=int, default=BOOTSTRAP_RESAMPLES)
    parser.add_argument("--output-dir", type=Path, default=HERE / "output")
    parser.add_argument("--no-public-mirror", action="store_true")
    parser.add_argument("--tag", type=str, default="")
    args = parser.parse_args()
    seeds = list(range(args.seed_start, args.seed_start + args.runs))
    scenario_codes = [c.strip() for c in args.scenarios.split(",") if c.strip()]
    tasks = build_tasks(seeds, scenario_codes)
    started = time.perf_counter()
    records: list[dict[str, Any]] = []
    if args.workers <= 1:
        for index, task in enumerate(tasks, start=1):
            record = run_one(task)
            records.append(record)
            if index % 10 == 0 or index == len(tasks):
                print(
                    f"[{index}/{len(tasks)}] {record['scenario']}/"
                    f"{record['variant']}/seed {record['seed']} "
                    f"score={record['score']:.4f} evals={record['evaluations']} "
                    f"({record['runtime_s']}s, total {time.perf_counter() - started:.0f}s)",
                    flush=True,
                )
    else:
        from multiprocessing import Pool

        with Pool(processes=args.workers) as pool:
            for index, record in enumerate(
                pool.imap_unordered(run_one, tasks, chunksize=1), start=1
            ):
                records.append(record)
                if index % 20 == 0 or index == len(tasks):
                    print(
                        f"[{index}/{len(tasks)}] {record['scenario']}/"
                        f"{record['variant']}/seed {record['seed']} "
                        f"score={record['score']:.4f} "
                        f"(total {time.perf_counter() - started:.0f}s)",
                        flush=True,
                    )
    records.sort(key=lambda r: (r["scenario"], r["variant"], int(r["seed"])))
    summary = summarize(records, args.bootstrap_resamples)
    suffix = f"_{args.tag}" if args.tag else ""
    stem = f"factorial_ablation{suffix}"
    destinations = [args.output_dir]
    if not args.no_public_mirror:
        destinations.append(PUBLIC_OUT)
    for directory in destinations:
        directory.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "scenario", "variant", "variant_label", "seed", "score",
            "evaluations", "directed_restarts", "max_trial_counter", "runtime_s",
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
