"""Table 4-10: SHDMS-ABC operational effects and efficiency on five datasets."""

from __future__ import annotations

import argparse
import numpy as np

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import write_dict_rows
from common.model import DATASET_SPECS, build_dataset_model
from common.paths import raw_output_path, table_output_path
from common.runtime import run_repeated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=50)
    args = parser.parse_args()
    runs, population, target = resolve_budget(args)
    records = []
    rows = []
    for dataset_index, (code, spec) in enumerate(DATASET_SPECS.items()):
        model = build_dataset_model(code)
        subset = run_repeated(model, ["SHDMS-ABC"], runs, population, target, args.limit, args.seed + dataset_index * 1000, code, "S1")
        records.extend(subset)
        rows.append({
            "Dataset": spec.name, "Average waiting time/min": f"{np.mean([r.average_waiting_time for r in subset]):.2f}",
            "Operating cost (Cq)": f"{np.mean([r.run_cost for r in subset]):.2f}",
            "Average load factor/%": f"{100 * np.mean([r.average_load for r in subset]):.2f}",
            "Maximum capacity utilization/%": f"{100 * np.mean([r.max_capacity_utilization for r in subset]):.2f}",
            "Daily trains": f"{np.mean([r.daily_departures for r in subset]):.1f}",
            "Runtime/s": f"{np.mean([r.runtime_s for r in subset]):.3f}",
        })
    output = table_output_path(10, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), [record.to_dict() for record in records])
    print(output)


if __name__ == "__main__":
    main()
