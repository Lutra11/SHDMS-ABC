"""表4-3：S3、S4 场景下各算法的性能、耗时、收敛代数与平均排名。"""

from __future__ import annotations

import argparse
from collections import defaultdict

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import fmt_mean_std, write_dict_rows
from common.model import build_dataset_model, create_scenario_model
from common.paths import raw_output_path, table_output_path
from common.runtime import CORE_ALGORITHMS, run_repeated
from common.statistics import mean_std, rank_values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=10)
    args = parser.parse_args()
    runs, population, target = resolve_budget(args)
    base = build_dataset_model("NST-HSR")
    records = []
    for scenario in ("S3", "S4"):
        model = create_scenario_model(base, scenario)
        records.extend(run_repeated(model, CORE_ALGORITHMS, runs, population, target, args.limit, args.seed + (3 if scenario == "S3" else 4) * 1000, "NST-HSR", scenario))
    grouped = defaultdict(list)
    for record in records:
        grouped[(record.scenario, record.algorithm)].append(record)
    scenario_ranks = {}
    for scenario in ("S3", "S4"):
        scenario_ranks[scenario] = rank_values({algorithm: mean_std([r.score for r in grouped[(scenario, algorithm)]])[0] for algorithm in CORE_ALGORITHMS})
    rows = []
    for algorithm in CORE_ALGORITHMS:
        s3 = [r.score for r in grouped[("S3", algorithm)]]
        s4 = [r.score for r in grouped[("S4", algorithm)]]
        all_records = grouped[("S3", algorithm)] + grouped[("S4", algorithm)]
        rows.append({
            "算法": algorithm, "S3/均值±标准差": fmt_mean_std(*mean_std(s3)),
            "S4/均值±标准差": fmt_mean_std(*mean_std(s4)),
            "平均CPU时间/s": f"{mean_std([r.runtime_s for r in all_records])[0]:.3f}",
            "平均收敛代数": f"{mean_std([r.convergence_cycle for r in all_records])[0]:.1f}",
            "平均排名": f"{(scenario_ranks['S3'][algorithm] + scenario_ranks['S4'][algorithm]) / 2:.2f}",
        })
    output = table_output_path(3, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), [record.to_dict() for record in records])
    print(output)


if __name__ == "__main__":
    main()
