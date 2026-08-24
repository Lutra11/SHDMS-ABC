"""Step 1: validate every source workbook and its cross-table dimensions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io_utils import write_dict_rows
from common.model import DATASET_SPECS, build_periods, find_bundle_files, load_factor_demands, load_station_capacities, load_timetable
from common.paths import DATASETS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DATASETS_DIR / "processed" / "validation_report.csv")
    args = parser.parse_args()
    report = []
    for code, spec in DATASET_SPECS.items():
        try:
            timetable, factors, capacity = find_bundle_files(spec)
            trains = load_timetable(timetable)
            stations = load_station_capacities(capacity)
            board, alight = load_factor_demands(factors, build_periods(), stations)
            if any(value < 0 for value in board.ravel()) or any(value < 0 for value in alight.ravel()):
                raise ValueError("客流需求不能为负数")
            report.append({"dataset": code, "status": "PASS", "timetable_rows": len(trains), "stations": len(stations), "factor_cells": board.size, "message": ""})
        except Exception as exc:
            report.append({"dataset": code, "status": "FAIL", "timetable_rows": "", "stations": "", "factor_cells": "", "message": str(exc)})
    write_dict_rows(args.output, report)
    print(f"validation report: {args.output}")
    if any(row["status"] == "FAIL" for row in report):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
