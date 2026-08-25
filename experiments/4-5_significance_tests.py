"""Table 4-5: Friedman and paired Wilcoxon tests across S1-S4."""

from __future__ import annotations

import argparse
from pathlib import Path

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import read_dict_rows, write_dict_rows
from common.model import build_dataset_model, create_scenario_model
from common.paths import raw_output_path, table_output_path
from common.runtime import CORE_ALGORITHMS, run_repeated
from common.statistics import a12_effect, block_mean_ranks, confidence_interval_95, holm_adjust, mean_std, paired_values, wilcoxon_signed_rank


REFERENCE = "SHDMS-ABC"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=10)
    parser.add_argument("--raw-input", type=Path, help="Read an existing run-level CSV and skip optimization")
    args = parser.parse_args()
    if args.raw_input:
        raw_rows = read_dict_rows(args.raw_input)
    else:
        runs, population, target = resolve_budget(args)
        base = build_dataset_model("NST-HSR")
        records = []
        for index, scenario in enumerate(("S1", "S2", "S3", "S4"), start=1):
            model = create_scenario_model(base, scenario)
            records.extend(run_repeated(model, CORE_ALGORITHMS, runs, population, target, args.limit, args.seed + index * 1000, "NST-HSR", scenario))
        raw_rows = [record.to_dict() for record in records]
    ranks = block_mean_ranks(raw_rows, CORE_ALGORITHMS)
    tests = {}
    for algorithm in CORE_ALGORITHMS:
        if algorithm == REFERENCE:
            continue
        reference, contender = paired_values(raw_rows, REFERENCE, algorithm)
        tests[algorithm] = (*wilcoxon_signed_rank(reference, contender), a12_effect(reference, contender), reference, contender)
    adjusted = holm_adjust({algorithm: values[1] for algorithm, values in tests.items()})
    rows = []
    order = [REFERENCE, *[name for name in CORE_ALGORITHMS if name != REFERENCE]]
    for algorithm in order:
        values = [float(row["score"]) for row in raw_rows if str(row["algorithm"]) == algorithm]
        avg, std = mean_std(values)
        low, high = confidence_interval_95(values)
        if algorithm == REFERENCE:
            statistic = raw_p = holm_p = effect = "—"
            result = "Baseline"
        else:
            statistic, raw_p, effect, reference, contender = tests[algorithm]
            holm_p = adjusted[algorithm]
            result = "+" if holm_p < 0.05 and sum(reference) < sum(contender) else ("-" if holm_p < 0.05 else "=")
            statistic, raw_p, holm_p, effect = f"{statistic:.1f}", f"{raw_p:.4g}", f"{holm_p:.4g}", f"{effect:.3f}"
        rows.append({
            "Algorithm": algorithm, "Mean": f"{avg:.4f}", "SD": f"{std:.4f}",
            "95% confidence interval": f"[{low:.4f}, {high:.4f}]", "Friedman mean rank": f"{ranks[algorithm]:.3f}",
            "Wilcoxon W": statistic, "Raw p": raw_p, "Holm-adjusted p": holm_p,
            "A12": effect, "Test result": result,
        })
    output = table_output_path(5, args.output)
    write_dict_rows(output, rows)
    if not args.raw_input:
        write_dict_rows(raw_output_path(output), raw_rows)
    print(output)


if __name__ == "__main__":
    main()
