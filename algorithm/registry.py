"""Algorithm registry and the common optimization entry point used by experiment scripts."""

from __future__ import annotations

from typing import List, Optional, Sequence

from .compared_algorithms.abc_family.abc import StandardABC
from .compared_algorithms.esa_family.cma_es import CMAESOptimizer
from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction
from .compared_algorithms.de_family.de import DEOptimizer
from .compared_algorithms.abc_family.gbest_abc import GbestABC
from .compared_algorithms.swarm_family.gwo import GWOOptimizer
from .compared_algorithms.swarm_family.hho import HHOOptimizer
from .compared_algorithms.de_family.ilshade_rsp import ILSHADERSPOptimizer
from .compared_algorithms.abc_family.iabc import IABC
from .compared_algorithms.de_family.jade import JADEOptimizer
from .compared_algorithms.de_family.lshade import LSHADEOptimizer
from .compared_algorithms.esa_family.lr_cma_es import LRCMAESOptimizer
from .compared_algorithms.abc_family.mabc import MABC
from .compared_algorithms.physics_family.mirime import MIRIMEOptimizer
from .compared_algorithms.abc_family.meabc import MeABC
from .compared_algorithms.swarm_family.pso import PSOOptimizer
from .compared_algorithms.de_family.qgdecc import QGDECCOptimizer
from .compared_algorithms.physics_family.rime import RIMEOptimizer
from shdms_abc_suite.optimizer.shdms_abc import run_shdms_abc  # alias bridge, see algorithm/__init__.py
from .compared_algorithms.swarm_family.sma import SMAOptimizer


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
