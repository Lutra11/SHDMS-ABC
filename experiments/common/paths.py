"""Repository paths used by all experiment and preprocessing scripts."""

from __future__ import annotations

import sys
from pathlib import Path


COMMON_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = COMMON_DIR.parent
GIT_CONTENT_DIR = EXPERIMENTS_DIR.parent
DATASETS_DIR = GIT_CONTENT_DIR / "datasets"
DATAS_DIR = GIT_CONTENT_DIR / "datas"


def ensure_import_paths() -> None:
    """Make the repository's ``algorithm`` package importable from any cwd."""

    path = str(GIT_CONTENT_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)


def table_output_path(table_no: int, output: str | Path | None = None) -> Path:
    """Resolve a table CSV path and create only its parent directory."""

    path = Path(output) if output else DATAS_DIR / f"table_4_{table_no}.csv"
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def raw_output_path(table_path: Path) -> Path:
    return table_path.with_name(f"{table_path.stem}_raw{table_path.suffix}")
