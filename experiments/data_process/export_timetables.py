"""Step 2: normalize all timetable workbooks to UTF-8 CSV files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io_utils import write_dict_rows
from common.model import DATASET_SPECS, find_bundle_files, load_timetable
from common.paths import DATASETS_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DATASETS_DIR / "processed")
    args = parser.parse_args()
    for code, spec in DATASET_SPECS.items():
        timetable, _, _ = find_bundle_files(spec)
        path = args.output_dir / code / "timetable.csv"
        write_dict_rows(path, load_timetable(timetable))
        print(path)


if __name__ == "__main__":
    main()
