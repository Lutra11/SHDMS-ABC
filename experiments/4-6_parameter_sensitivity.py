"""表4-6：βw、ρH、τD 与 LR 的单因素参数敏感性。"""

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
    ("状态匹配影响强度", "βw", "beta", [0.50, 1.00, 1.50]),
    ("历史信用更新系数", "ρH", "history_rate", [0.10, 0.50, 0.90]),
    ("种群多样性阈值", "τD", "diversity_low_threshold", [0.02, 0.10, 0.20]),
    ("重启触发阈值", "LR", "limit", [10, 30, 50]),
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
                    "参数类别": name, "参数符号": symbol, "参数值": value, "run": offset + 1,
                    "score": benchmark_score(metrics), "feasible": hard_violation(metrics) <= 1e-9,
                    "convergence_cycle": convergence_cycle(result.convergence_history), "runtime_s": elapsed,
                })
    grouped = defaultdict(list)
    for row in raw:
        grouped[(row["参数符号"], row["参数值"])].append(row)
    rows = []
    for name, symbol, _, values in PARAMETERS:
        for value in values:
            subset = grouped[(symbol, value)]
            scores = [float(row["score"]) for row in subset]
            rows.append({
                "参数类别": name, "参数设置": f"{symbol}={value:g}", "最优值": f"{min(scores):.4f}",
                "均值±标准差": fmt_mean_std(*mean_std(scores)),
                "可行率/%": f"{100 * sum(bool(row['feasible']) for row in subset) / len(subset):.1f}",
                "平均收敛代数": f"{np.mean([row['convergence_cycle'] for row in subset]):.1f}",
                "平均运行时间/s": f"{np.mean([row['runtime_s'] for row in subset]):.3f}",
            })
    output = table_output_path(6, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), raw)
    print(output)


if __name__ == "__main__":
    main()
