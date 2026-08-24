"""表4-9：五项约束惩罚系数在 ×0.5/×2.0 扰动下的鲁棒性。"""

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
        "参数方案": row["参数方案"], "扰动水平": row["扰动水平"], "MARD_h/%": f"{row['MARD_h/%']:.2f}",
        "平均约束违反量": f"{row['平均约束违反量']:.6f}", "最大约束违反量": f"{row['最大约束违反量']:.6f}",
        "可行率/%": f"{row['可行率/%']:.1f}", "平均运行时间/s": f"{row['平均运行时间/s']:.3f}",
        "时间变化/%": f"{row['时间变化/%']:.2f}",
    } for row in summary]
    output = table_output_path(9, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), raw)
    print(output)


if __name__ == "__main__":
    main()
