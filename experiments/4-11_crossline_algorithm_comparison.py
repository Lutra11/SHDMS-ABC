"""Table 4-11: Algorithm objectives and cross-dataset mean ranks."""

from __future__ import annotations

import argparse
from collections import defaultdict

from common.cli import add_budget_arguments, resolve_budget
from common.io_utils import fmt_mean_std, write_dict_rows
from common.model import DATASET_SPECS, build_dataset_model
from common.paths import raw_output_path, table_output_path
from common.runtime import CROSSLINE_ALGORITHMS, run_repeated
from common.statistics import mean_std, rank_values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_budget_arguments(parser, runs=50)
    args = parser.parse_args()
    runs, population, target = resolve_budget(args)
    records = []
    rank_accumulator = defaultdict(list)
    rows = []
    for dataset_index, (code, spec) in enumerate(DATASET_SPECS.items()):
        model = build_dataset_model(code)
        subset = run_repeated(model, CROSSLINE_ALGORITHMS, runs, population, target, args.limit, args.seed + dataset_index * 1000, code, "S1")
        records.extend(subset)
        values = {algorithm: [r.score for r in subset if r.algorithm == algorithm] for algorithm in CROSSLINE_ALGORITHMS}
        ranks = rank_values({algorithm: mean_std(scores)[0] for algorithm, scores in values.items()})
        row = {"Dataset": spec.name}
        for algorithm in CROSSLINE_ALGORITHMS:
            row[algorithm] = fmt_mean_std(*mean_std(values[algorithm]))
            rank_accumulator[algorithm].append(ranks[algorithm])
        rows.append(row)
    rows.append({"Dataset": "Average rank"} | {algorithm: f"{sum(rank_accumulator[algorithm]) / len(rank_accumulator[algorithm]):.2f}" for algorithm in CROSSLINE_ALGORITHMS})
    output = table_output_path(11, args.output)
    write_dict_rows(output, rows)
    write_dict_rows(raw_output_path(output), [record.to_dict() for record in records])
    print(output)


if __name__ == "__main__":
    main()
