"""Table 4-9: Robustness of five penalty coefficients under 0.5x and 2.0x perturbations."""

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
    raw, summary = run_robustness("penalty", runs, population, target, args.limit, args.seed)
    rows = [{
        "Parameter setting": row["Parameter setting"], "Perturbation level": row["Perturbation level"], "MARD_h/%": f"{row['MARD_h/%']:.2f}",
        "Mean constraint violation": f"{row['Mean constraint violation']:.6f}", "Maximum constraint violation": f"{row['Maximum constraint violation']:.6f}",
        "Feasible rate/%": f"{row['Feasible rate/%']:.1f}", "Mean runtime/s": f"{row['Mean runtime/s']:.3f}",
        "Runtime change/%": f"{row['Runtime change/%']:.2f}",
    } for row in summary]
    output = table_output_path(9, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), raw)
    print(output)


if __name__ == "__main__":
    main()
