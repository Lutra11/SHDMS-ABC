"""Table 4-7: Ablation study of four SHDMS-ABC mechanisms."""

from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import fmt_mean_std, write_dict_rows
from common.model import benchmark_score, build_dataset_model
from common.paths import raw_output_path, table_output_path
from common.runtime import convergence_cycle, cycles_for_budget, run_variant
from common.statistics import a12_effect, holm_adjust, mean_std, wilcoxon_signed_rank


VARIANTS = ["SHDMS-ABC", "w/o OW", "w/o SH", "w/o DT", "w/o RS", "Basic ABC"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=10)
    args = parser.parse_args()
    runs, population, target = resolve_budget(args)
    max_cycles = cycles_for_budget("SHDMS-ABC", target, population)
    model = build_dataset_model("NST-HSR")
    raw = []
    for variant in VARIANTS:
        for offset in range(runs):
            result, metrics, elapsed = run_variant(model, variant, args.seed + offset, population, max_cycles, args.limit)
            raw.append({"variant": variant, "run": offset + 1, "score": benchmark_score(metrics), "convergence_cycle": convergence_cycle(result.convergence_history), "runtime_s": elapsed})
    grouped = defaultdict(list)
    for row in raw:
        grouped[row["variant"]].append(row)
    reference = [float(row["score"]) for row in grouped["SHDMS-ABC"]]
    tests = {}
    for variant in VARIANTS[1:]:
        contender = [float(row["score"]) for row in grouped[variant]]
        tests[variant] = (*wilcoxon_signed_rank(reference, contender), a12_effect(reference, contender), contender)
    adjusted = holm_adjust({variant: test[1] for variant, test in tests.items()})
    rows = []
    for variant in VARIANTS:
        subset = grouped[variant]
        scores = [float(row["score"]) for row in subset]
        if variant == "SHDMS-ABC":
            raw_p = holm_p = effect = result_text = "—"
        else:
            _, p_value, a12, contender = tests[variant]
            raw_p, holm_p, effect = f"{p_value:.4g}", f"{adjusted[variant]:.4g}", f"{a12:.3f}"
            result_text = "+" if adjusted[variant] < 0.05 and np.mean(reference) < np.mean(contender) else ("-" if adjusted[variant] < 0.05 else "=")
        rows.append({
            "Variant": variant, "Best": f"{min(scores):.4f}", "Mean±SD": fmt_mean_std(*mean_std(scores)),
            "Mean convergence cycle": f"{np.mean([row['convergence_cycle'] for row in subset]):.1f}",
            "Mean runtime/s": f"{np.mean([row['runtime_s'] for row in subset]):.3f}",
            "Raw p": raw_p, "Holm p": holm_p, "A12": effect, "Result": result_text,
        })
    output = table_output_path(7, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), raw)
    print(output)


if __name__ == "__main__":
    main()
