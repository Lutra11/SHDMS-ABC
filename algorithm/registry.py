"""Algorithm registry and the common optimization entry point used by experiment scripts."""

from __future__ import annotations

from typing import List, Optional, Sequence

from .abc import StandardABC
from .cma_es import CMAESOptimizer
from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction
from .de import DEOptimizer
from .gbest_abc import GbestABC
from .gwo import GWOOptimizer
from .hho import HHOOptimizer
from .ilshade_rsp import ILSHADERSPOptimizer
from .iabc import IABC
from .jade import JADEOptimizer
from .lshade import LSHADEOptimizer
from .lr_cma_es import LRCMAESOptimizer
from .mabc import MABC
from .mirime import MIRIMEOptimizer
from .meabc import MeABC
from .pso import PSOOptimizer
from .qgdecc import QGDECCOptimizer
from .rime import RIMEOptimizer
from .shdms_abc import run_shdms_abc
from .sma import SMAOptimizer


def optimize_algorithm(
    algorithm_name: str,
    objective: ObjectiveFunction,
    bounds: Bounds,
    config: GenericConfig,
    seed_solutions: Optional[Sequence[Sequence[float]]] = None,
) -> AlgorithmResult:
    name = algorithm_name.upper()
    if name == "ABC":
        return StandardABC(objective, bounds, config).optimize()
    if name == "GBEST-ABC":
        return GbestABC(objective, bounds, config).optimize()
    if name == "MABC":
        return MABC(objective, bounds, config).optimize()
    if name == "MEABC":
        return MeABC(objective, bounds, config).optimize()
    if name == "IABC":
        return IABC(objective, bounds, config).optimize()
    if name == "PSO":
        return PSOOptimizer(objective, bounds, config).optimize()
    if name == "DE":
        return DEOptimizer(objective, bounds, config).optimize()
    if name == "JADE":
        return JADEOptimizer(objective, bounds, config).optimize()
    if name in {"LSHADE", "L-SHADE"}:
        return LSHADEOptimizer(objective, bounds, config).optimize()
    if name in {"ILSHADE-RSP", "ILSHADERSP", "I-LSHADE-RSP"}:
        return ILSHADERSPOptimizer(objective, bounds, config).optimize()
    if name == "QGDECC":
        return QGDECCOptimizer(objective, bounds, config).optimize()
    if name in {"CMA-ES", "CMAES"}:
        return CMAESOptimizer(objective, bounds, config).optimize()
    if name in {"LR-CMA-ES", "LRCMAES", "LR-CMAES", "LRA-CMA-ES"}:
        return LRCMAESOptimizer(objective, bounds, config).optimize()
    if name == "GWO":
        return GWOOptimizer(objective, bounds, config).optimize()
    if name == "HHO":
        return HHOOptimizer(objective, bounds, config).optimize()
    if name == "SMA":
        return SMAOptimizer(objective, bounds, config).optimize()
    if name == "RIME":
        return RIMEOptimizer(objective, bounds, config).optimize()
    if name in {"MIRIME", "MI-RIME"}:
        return MIRIMEOptimizer(objective, bounds, config).optimize()
    if name == "SHDMS-ABC":
        return run_shdms_abc(objective, bounds, config, seed_solutions=seed_solutions)
    raise ValueError(f"Unsupported algorithm: {algorithm_name}")


def algorithm_display_names() -> List[str]:
    """Return the eight algorithms used in the manuscript baseline table."""
    return ["ABC", "Gbest-ABC", "MeABC", "IABC", "PSO", "DE", "GWO", "SHDMS-ABC"]


def all_algorithm_names() -> List[str]:
    """Return every algorithm implemented in this submission file."""
    return [
        "ABC",
        "Gbest-ABC",
        "MeABC",
        "MABC",
        "IABC",
        "PSO",
        "DE",
        "JADE",
        "LSHADE",
        "iLSHADE-RSP",
        "QGDECC",
        "CMA-ES",
        "LR-CMA-ES",
        "GWO",
        "HHO",
        "SMA",
        "RIME",
        "MIRIME",
        "SHDMS-ABC",
    ]
