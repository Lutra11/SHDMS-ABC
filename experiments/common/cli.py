"""Consistent command-line parameters for all table reproduction scripts."""

from __future__ import annotations

import argparse
from pathlib import Path


def add_budget_arguments(
    parser: argparse.ArgumentParser,
    *,
    runs: int = 10,
    population: int = 30,
    target_evaluations: int = 6000,
    limit: int = 30,
    seed: int = 2026082201,
) -> None:
    parser.add_argument("--runs", type=int, default=runs, help="独立运行次数")
    parser.add_argument("--population", type=int, default=population, help="种群规模")
    parser.add_argument("--target-evaluations", type=int, default=target_evaluations, help="目标函数评价预算（目标值）")
    parser.add_argument("--limit", type=int, default=limit, help="连续未改进/重启阈值")
    parser.add_argument("--seed", type=int, default=seed, help="首个随机种子")
    parser.add_argument("--output", type=Path, help="汇总 CSV 输出路径")
    parser.add_argument("--smoke", action="store_true", help="使用极小预算验证代码链路")


def resolve_budget(args: argparse.Namespace) -> tuple[int, int, int]:
    if args.runs <= 0 or args.population < 4 or args.target_evaluations <= 0:
        raise ValueError("runs/target-evaluations 必须为正数，population 至少为 4")
    if args.smoke:
        return 1, 6, 120
    return args.runs, args.population, args.target_evaluations
