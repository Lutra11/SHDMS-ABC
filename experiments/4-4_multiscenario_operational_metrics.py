"""Table 4-4: Operational metrics for representative solutions in S1-S4."""

from __future__ import annotations

import argparse
from collections import defaultdict

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import write_dict_rows
from common.model import build_dataset_model, create_scenario_model
from common.paths import raw_output_path, table_output_path
from common.runtime import OPERATIONAL_ALGORITHMS, run_repeated


def representative(records):
    return min(records, key=lambda row: (not row.feasible, row.hard_violation, row.soft_violation, row.objective, row.average_waiting_time))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=10)
    args = parser.parse_args()
    runs, population, target = resolve_budget(args)
    base = build_dataset_model("NST-HSR")
    records = []
    for index, scenario in enumerate(("S1", "S2", "S3", "S4"), start=1):
        model = create_scenario_model(base, scenario)
        records.extend(run_repeated(model, OPERATIONAL_ALGORITHMS, runs, population, target, args.limit, args.seed + index * 1000, "NST-HSR", scenario))
    grouped = defaultdict(list)
    for record in records:
        grouped[(record.scenario, record.algorithm)].append(record)
    rows = []
    for scenario in ("S1", "S2", "S3", "S4"):
        for algorithm in OPERATIONAL_ALGORITHMS:
            row = representative(grouped[(scenario, algorithm)])
            rows.append({
                "Scenario": scenario, "Algorithm": "SHDMS" if algorithm == "SHDMS-ABC" else algorithm,
                "Mean waiting time/min": f"{row.average_waiting_time:.2f}",
                "Average load factor/%": f"{row.average_load * 100:.2f}",
                "Daily departures": row.daily_departures, "Composite objective F": f"{row.objective:.4f}",
                "Feasible": "Yes" if row.feasible else "No",
            })
    output = table_output_path(4, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), [record.to_dict() for record in records])
    print(output)


if __name__ == "__main__":
    main()
