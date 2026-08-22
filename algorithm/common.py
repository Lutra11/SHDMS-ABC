"""Shared type aliases, configurations, and result containers for the optimization algorithms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

import numpy as np


Vector = np.ndarray
Bounds = Sequence[Tuple[float, float]]
ObjectiveFunction = Callable[[Sequence[float]], float]


@dataclass
class GenericConfig:
    population: int = 24
    max_cycles: int = 80
    limit: int = 30
    seed: Optional[int] = None


@dataclass
class AlgorithmResult:
    best_position: List[float]
    best_value: float
    convergence_history: List[float]
    evaluations: int
