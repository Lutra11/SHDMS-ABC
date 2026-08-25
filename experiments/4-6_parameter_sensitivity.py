"""Table 4-6: One-factor sensitivity of beta_w, rho_H, tau_D and L_R."""

from __future__ import annotations

import argparse
from collections import defaultdict

import numpy as np

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import fmt_mean_std, write_dict_rows
from common.model import benchmark_score, build_dataset_model, hard_violation
from common.paths import raw_output_path, table_output_path
from common.runtime import convergence_cycle, cycles_for_budget, run_variant
from common.statistics import mean_std


# These baselines reproduce the parameter levels printed in the supplied Table 4-6.
BASELINE = {"beta": 1.00, "history_rate": 0.50, "diversity_low_threshold": 0.10}
PARAMETERS = [
    ("State-matching influence", "βw", "beta", [0.50, 1.00, 1.50]),
    ("Success-history update rate", "ρH", "history_rate", [0.10, 0.50, 0.90]),
    ("Population-diversity threshold", "τD", "diversity_low_threshold", [0.02, 0.10, 0.20]),
    ("Restart trigger threshold", "LR", "limit", [10, 30, 50]),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=10)
    args = parser.parse_args()
    runs, population, target = resolve_budget(args)
    max_cycles = cycles_for_budget("SHDMS-ABC", target, population)
    model = build_dataset_model("NST-HSR")
    raw = []
    for name, symbol, key, values in PARAMETERS:
        for value in values:
            overrides = dict(BASELINE)
            actual_limit = args.limit
            if key == "limit":
                actual_limit = int(value)
            else:
                overrides[key] = value
            for offset in range(runs):
                result, metrics, elapsed = run_variant(model, "SHDMS-ABC", args.seed + offset, population, max_cycles, actual_limit, overrides)
                raw.append({
                    "parameter_category": name, "parameter_symbol": symbol, "parameter_value": value, "run": offset + 1,
                    "score": benchmark_score(metrics), "feasible": hard_violation(metrics) <= 1e-9,
                    "convergence_cycle": convergence_cycle(result.convergence_history), "runtime_s": elapsed,
                })
    grouped = defaultdict(list)
    for row in raw:
        grouped[(row["parameter_symbol"], row["parameter_value"])].append(row)
    rows = []
    for name, symbol, _, values in PARAMETERS:
        for value in values:
            subset = grouped[(symbol, value)]
            scores = [float(row["score"]) for row in subset]
            rows.append({
                "Parameter category": name, "Parameter setting": f"{symbol}={value:g}", "Best": f"{min(scores):.4f}",
                "Mean±SD": fmt_mean_std(*mean_std(scores)),
                "Feasible rate/%": f"{100 * sum(bool(row['feasible']) for row in subset) / len(subset):.1f}",
                "Mean convergence cycle": f"{np.mean([row['convergence_cycle'] for row in subset]):.1f}",
                "Mean runtime/s": f"{np.mean([row['runtime_s'] for row in subset]):.3f}",
            })
    output = table_output_path(6, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), raw)
    print(output)


if __name__ == "__main__":
    main()
