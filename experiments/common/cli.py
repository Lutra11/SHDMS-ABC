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
    parser.add_argument("--runs", type=int, default=runs, help="Number of independent runs")
    parser.add_argument("--population", type=int, default=population, help="Population size")
    parser.add_argument("--target-evaluations", type=int, default=target_evaluations, help="Target objective-evaluation budget")
    parser.add_argument("--limit", type=int, default=limit, help="Stagnation or restart threshold")
    parser.add_argument("--seed", type=int, default=seed, help="First random seed")
    parser.add_argument("--output", type=Path, help="Summary CSV output path")
    parser.add_argument("--smoke", action="store_true", help="Use a minimal budget to verify the execution path")


def resolve_budget(args: argparse.Namespace) -> tuple[int, int, int]:
    if args.runs <= 0 or args.population < 4 or args.target_evaluations <= 0:
        raise ValueError("runs and target-evaluations must be positive, and population must be at least 4")
    if args.smoke:
        return 1, 6, 120
    return args.runs, args.population, args.target_evaluations
