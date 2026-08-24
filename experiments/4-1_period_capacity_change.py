"""表4-1：分时段运力配置优化前后对比。"""

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
    baseline = model.base.evaluate_vector(model.baseline_vector())
    _, _, optimized = run_algorithm(model, "SHDMS-ABC", args.seed, population, target, args.limit, use_seed_solutions=True)
    rows = []
    for index, period in enumerate(model.base.periods):
        demand = float(np.sum(model.base.board_demand[index]))
        original, new = baseline.intervals[index], optimized.intervals[index]
        rows.append({
            "时段标号k": period.index, "时间段": period.label, "时段客流量/人": round(demand),
            "小时客流量/(人·h^-1)": round(demand / (period.duration_min / 60)),
            "发车数量/原方案": int(baseline.departures[index]), "发车数量/优化方案": int(optimized.departures[index]),
            "发车间隔min/原方案": f"{original:.2f}", "发车间隔min/优化方案": f"{new:.2f}",
            "变化量/min": f"{new - original:.2f}", "变化率/%": f"{(new - original) / original * 100:.2f}",
        })
    rows.append({
        "时段标号k": "合计/均值", "时间段": "06:00-22:00",
        "时段客流量/人": round(sum(float(r["时段客流量/人"]) for r in rows)),
        "小时客流量/(人·h^-1)": round(sum(float(r["时段客流量/人"]) for r in rows) / 16),
        "发车数量/原方案": int(np.sum(baseline.departures)), "发车数量/优化方案": int(np.sum(optimized.departures)),
        "发车间隔min/原方案": f"{baseline.weighted_interval:.2f}", "发车间隔min/优化方案": f"{optimized.weighted_interval:.2f}",
        "变化量/min": f"{optimized.weighted_interval - baseline.weighted_interval:.2f}",
        "变化率/%": f"{(optimized.weighted_interval - baseline.weighted_interval) / baseline.weighted_interval * 100:.2f}",
    })
    output = table_output_path(1, args.output)
    write_dict_rows(output, rows)
    print(output)


if __name__ == "__main__":
    main()
