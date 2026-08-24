"""Step 3: export period-by-station boarding and alighting demand."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io_utils import write_dict_rows
from common.model import DATASET_SPECS, build_periods, find_bundle_files, load_factor_demands, load_station_capacities
from common.paths import DATASETS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DATASETS_DIR / "processed")
    args = parser.parse_args()
    periods = build_periods()
    for code, spec in DATASET_SPECS.items():
        _, factors, capacity = find_bundle_files(spec)
        stations = load_station_capacities(capacity)
        board, alight = load_factor_demands(factors, periods, stations)
        rows = []
        for pi, period in enumerate(periods):
            for si, station in enumerate(stations):
                rows.append({"period_index": period.index, "period_label": period.label, "station_name": station.name, "boarding_demand": board[pi, si], "alighting_demand": alight[pi, si]})
        path = args.output_dir / code / "demand_factors.csv"
        write_dict_rows(path, rows)
        print(path)


if __name__ == "__main__":
    main()
