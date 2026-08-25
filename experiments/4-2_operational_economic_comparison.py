"""Table 4-2: Operational, economic and constraint metrics."""

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
        ("Operating cost", original.run_cost, optimized.run_cost),
        ("Passenger waiting cost", original.wait_cost, optimized.wait_cost),
        ("Target occupancy loss", original.occupancy_loss, optimized.occupancy_loss),
        ("Dwell adjustment cost", original.stop_adjustment_cost, optimized.stop_adjustment_cost),
        ("Ticket revenue", original.revenue, optimized.revenue),
        ("Average load factor/%", original.average_load * 100, optimized.average_load * 100),
        ("Maximum capacity utilization/%", original.max_capacity_utilization * 100, optimized.max_capacity_utilization * 100),
        ("Daily departures", np.sum(original.departures), np.sum(optimized.departures)),
        ("Composite objective F", original.objective, optimized.objective),
    ]
    rows = [{"Metric": name, "Baseline": f"{before:.4f}", "Optimized": f"{after:.4f}", "Relative change/%": f"{(after - before) / max(abs(before), 1e-12) * 100:.2f}"} for name, before, after in metrics]
    output = table_output_path(2, args.output)
    write_dict_rows(output, rows)
    print(output)


if __name__ == "__main__":
    main()
