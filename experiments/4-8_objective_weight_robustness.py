"""表4-8：四项归一化目标权重在 ±25% 扰动下的鲁棒性。"""

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
        "参数方案": row["参数方案"], "扰动水平": row["扰动水平"],
        "MARD_h/%": f"{row['MARD_h/%']:.2f}", "最大时段偏差/min": f"{row['最大时段偏差/min']:.2f}",
        "开行数量变化/列": f"{row['开行数量变化/列']:.2f}", "等待成本变化/%": f"{row['等待成本变化/%']:.2f}",
        "运营成本变化/%": f"{row['运营成本变化/%']:.2f}", "可行率/%": f"{row['可行率/%']:.1f}",
    } for row in summary]
    output = table_output_path(8, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), raw)
    print(output)


if __name__ == "__main__":
    main()
