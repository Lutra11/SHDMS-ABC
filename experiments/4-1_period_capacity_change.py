"""Table 4-1: Period capacity allocation before and after optimization."""

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
            "Period index k": period.index, "Period": period.label, "Period demand/passengers": round(demand),
            "Hourly demand/(passengers h^-1)": round(demand / (period.duration_min / 60)),
            "Departures/Baseline": int(baseline.departures[index]), "Departures/Optimized": int(optimized.departures[index]),
            "Headway min/Baseline": f"{original:.2f}", "Headway min/Optimized": f"{new:.2f}",
            "Change/min": f"{new - original:.2f}", "Change/%": f"{(new - original) / original * 100:.2f}",
        })
    rows.append({
        "Period index k": "Total/Mean", "Period": "06:00-22:00",
        "Period demand/passengers": round(sum(float(r["Period demand/passengers"]) for r in rows)),
        "Hourly demand/(passengers h^-1)": round(sum(float(r["Period demand/passengers"]) for r in rows) / 16),
        "Departures/Baseline": int(np.sum(baseline.departures)), "Departures/Optimized": int(np.sum(optimized.departures)),
        "Headway min/Baseline": f"{baseline.weighted_interval:.2f}", "Headway min/Optimized": f"{optimized.weighted_interval:.2f}",
        "Change/min": f"{optimized.weighted_interval - baseline.weighted_interval:.2f}",
        "Change/%": f"{(optimized.weighted_interval - baseline.weighted_interval) / baseline.weighted_interval * 100:.2f}",
    })
    output = table_output_path(1, args.output)
    write_dict_rows(output, rows)
    print(output)


if __name__ == "__main__":
    main()
