"""表4-2：原方案与优化方案的运营、经济及约束指标。"""

from __future__ import annotations

import argparse
import numpy as np

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import write_dict_rows
from common.model import build_dataset_model
from common.paths import table_output_path
from common.runtime import run_algorithm


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=1)
    args = parser.parse_args()
    _, population, target = resolve_budget(args)
    model = build_dataset_model("NST-HSR")
    original = model.base.evaluate_vector(model.baseline_vector())
    _, _, optimized = run_algorithm(model, "SHDMS-ABC", args.seed, population, target, args.limit, use_seed_solutions=True)
    metrics = [
        ("企业运行成本", original.run_cost, optimized.run_cost),
        ("旅客等待成本", original.wait_cost, optimized.wait_cost),
        ("目标上座损失", original.occupancy_loss, optimized.occupancy_loss),
        ("停站调整成本", original.stop_adjustment_cost, optimized.stop_adjustment_cost),
        ("票务收入", original.revenue, optimized.revenue),
        ("平均载客率/%", original.average_load * 100, optimized.average_load * 100),
        ("最大能力利用率/%", original.max_capacity_utilization * 100, optimized.max_capacity_utilization * 100),
        ("日开行总车次", np.sum(original.departures), np.sum(optimized.departures)),
        ("综合目标值F", original.objective, optimized.objective),
    ]
    rows = [{"指标": name, "原方案": f"{before:.4f}", "优化方案": f"{after:.4f}", "相对变化/%": f"{(after - before) / max(abs(before), 1e-12) * 100:.2f}"} for name, before, after in metrics]
    output = table_output_path(2, args.output)
    write_dict_rows(output, rows)
    print(output)


if __name__ == "__main__":
    main()
