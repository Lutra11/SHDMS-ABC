"""Step 4: export standardized station/platform capacity data."""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io_utils import write_dict_rows
from common.model import DATASET_SPECS, find_bundle_files, load_station_capacities
from common.paths import DATASETS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DATASETS_DIR / "processed")
    args = parser.parse_args()
    for code, spec in DATASET_SPECS.items():
        _, _, capacity = find_bundle_files(spec)
        path = args.output_dir / code / "station_capacity.csv"
        write_dict_rows(path, [asdict(station) for station in load_station_capacities(capacity)])
        print(path)


if __name__ == "__main__":
    main()
