"""Statistics used by tables 4-3 through 4-11.

The implementation intentionally avoids an undeclared SciPy dependency.  It
uses the normal approximation for paired Wilcoxon p-values, matching the
fallback used to prepare the supplied supplementary results.
"""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean
from typing import Iterable, Mapping, Sequence

import numpy as np


def mean_std(values: Sequence[float], ddof: int = 0) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return math.nan, math.nan
    return float(np.mean(array)), float(np.std(array, ddof=ddof))


def confidence_interval_95(values: Sequence[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    if array.size <= 1:
        value = float(array[0]) if array.size else math.nan
        return value, value
    center = float(np.mean(array))
    half = 1.96 * float(np.std(array, ddof=1)) / math.sqrt(array.size)
    return center - half, center + half


def rank_values(values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda item: item[1])
    result: dict[str, float] = {}
    index = 0
    while index < len(ordered):
        end = index
        while end + 1 < len(ordered) and abs(ordered[end + 1][1] - ordered[index][1]) <= 1e-12:
            end += 1
        average_rank = (index + 1 + end + 1) / 2.0
        for offset in range(index, end + 1):
            result[ordered[offset][0]] = average_rank
        index = end + 1
    return result


def block_mean_ranks(
    rows: Iterable[Mapping[str, object]],
    algorithms: Sequence[str],
    block_fields: Sequence[str] = ("scenario", "run"),
    score_field: str = "score",
) -> dict[str, float]:
    blocks: dict[tuple[object, ...], dict[str, float]] = defaultdict(dict)
    for row in rows:
        algorithm = str(row["algorithm"])
        if algorithm in algorithms:
            key = tuple(row[field] for field in block_fields)
            blocks[key][algorithm] = float(row[score_field])
    rank_lists: dict[str, list[float]] = {name: [] for name in algorithms}
    for scores in blocks.values():
        if not all(name in scores for name in algorithms):
            continue
        ranks = rank_values(scores)
        for name in algorithms:
            rank_lists[name].append(ranks[name])
    return {
        name: float(np.mean(values)) if values else math.nan
        for name, values in rank_lists.items()
    }


def a12_effect(reference: Sequence[float], contender: Sequence[float]) -> float:
    wins = 0.0
    for x in reference:
        for y in contender:
            if x < y:
                wins += 1.0
            elif x == y:
                wins += 0.5
    return wins / max(len(reference) * len(contender), 1)


def wilcoxon_signed_rank(x: Sequence[float], y: Sequence[float]) -> tuple[float, float]:
    diffs = [float(a) - float(b) for a, b in zip(x, y)]
    nonzero = [value for value in diffs if abs(value) > 1e-12]
    if not nonzero:
        return 0.0, 1.0
    magnitudes = [abs(value) for value in nonzero]
    order = sorted(range(len(magnitudes)), key=magnitudes.__getitem__)
    ranks = [0.0] * len(order)
    index = 0
    while index < len(order):
        end = index
        while end + 1 < len(order) and abs(magnitudes[order[end + 1]] - magnitudes[order[index]]) <= 1e-12:
            end += 1
        average_rank = (index + 1 + end + 1) / 2.0
        for offset in range(index, end + 1):
            ranks[order[offset]] = average_rank
        index = end + 1
    w_positive = sum(rank for rank, diff in zip(ranks, nonzero) if diff > 0)
    w_negative = sum(rank for rank, diff in zip(ranks, nonzero) if diff < 0)
    statistic = min(w_positive, w_negative)
    n = len(nonzero)
    expected = n * (n + 1) / 4.0
    variance = n * (n + 1) * (2 * n + 1) / 24.0
    if variance <= 0:
        return float(statistic), 1.0
    z = (statistic - expected + 0.5) / math.sqrt(variance)
    p_value = math.erfc(abs(z) / math.sqrt(2.0))
    return float(statistic), float(min(max(p_value, 0.0), 1.0))


def holm_adjust(p_values: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for index, (name, value) in enumerate(ordered):
        current = min(1.0, (count - index) * float(value))
        running = max(running, current)
        adjusted[name] = running
    return adjusted


def paired_values(
    rows: Iterable[Mapping[str, object]],
    reference: str,
    contender: str,
    block_fields: Sequence[str] = ("scenario", "run"),
    score_field: str = "score",
) -> tuple[list[float], list[float]]:
    reference_map: dict[tuple[object, ...], float] = {}
    contender_map: dict[tuple[object, ...], float] = {}
    for row in rows:
        key = tuple(row[field] for field in block_fields)
        if row["algorithm"] == reference:
            reference_map[key] = float(row[score_field])
        elif row["algorithm"] == contender:
            contender_map[key] = float(row[score_field])
    keys = sorted(set(reference_map).intersection(contender_map))
    return [reference_map[key] for key in keys], [contender_map[key] for key in keys]


def average(values: Sequence[float]) -> float:
    return float(mean(values)) if values else math.nan
