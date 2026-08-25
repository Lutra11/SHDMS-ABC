"""Table 4-8: Robustness of normalized objective weights under ±25% perturbations."""

from __future__ import annotations

import argparse

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import write_dict_rows
from common.paths import raw_output_path, table_output_path
from common.robustness import run_robustness


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=5)
    args = parser.parse_args()
    runs, population, target = resolve_budget(args)
    raw, summary = run_robustness("weight", runs, population, target, args.limit, args.seed)
    rows = [{
        "Parameter setting": row["Parameter setting"], "Perturbation level": row["Perturbation level"],
        "MARD_h/%": f"{row['MARD_h/%']:.2f}", "Maximum period deviation/min": f"{row['Maximum period deviation/min']:.2f}",
        "Departure change/trains": f"{row['Departure change/trains']:.2f}", "Waiting cost change/%": f"{row['Waiting cost change/%']:.2f}",
        "Operating cost change/%": f"{row['Operating cost change/%']:.2f}", "Feasible rate/%": f"{row['Feasible rate/%']:.1f}",
    } for row in summary]
    output = table_output_path(8, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), raw)
    print(output)


if __name__ == "__main__":
    main()
