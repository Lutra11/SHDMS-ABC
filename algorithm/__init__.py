"""Optimization algorithms used by the SHDMS-ABC experiments.

Layout (reorganized October 2026)
----------------------------------
algorithm/
├── __init__.py            this facade; importlib bridge for shdms-abc/
├── common.py              shared types (GenericConfig, AlgorithmResult, ...)
├── registry.py            uniform dispatch entry point optimize_algorithm()
├── shdms-abc/             the proposed SHDMS-ABC suite (not a package; see below)
│   ├── modeling/          joint headway-dwell optimization model (Secs 3.1.1-3.1.4)
│   ├── optimizer/         SHDMS-ABC optimizer (Sec 3.2)
│   └── README.md          layered-structure notes
└── compared_algorithms/    18 baseline optimizers grouped by family
    ├── abc_family/        ABC, Gbest-ABC, MeABC, MABC, IABC
    ├── de_family/         DE, JADE, L-SHADE, iLSHADE-RSP, QGDECC
    ├── esa_family/        CMA-ES, LR-CMA-ES
    ├── swarm_family/      PSO, GWO, HHO, SMA
    └── physics_family/    RIME, MIRIME

The proposed-method folder is named ``shdms-abc`` (hyphen) for clarity on disk
and in the repository tree, which makes it invalid as a Python package name.
This facade therefore loads its two layers explicitly with importlib under the
alias package ``shdms_abc_suite`` BEFORE importing the registry, so the
registry (and downstream code) can import from that alias normally.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .common import AlgorithmResult, Bounds, GenericConfig, ObjectiveFunction, Vector

# --------------------------------------------------------- comparison set ---

from .compared_algorithms.abc_family.abc import StandardABC
from .compared_algorithms.abc_family.gbest_abc import GbestABC
from .compared_algorithms.abc_family.meabc import MeABC
from .compared_algorithms.abc_family.mabc import MABC
from .compared_algorithms.abc_family.iabc import IABC
from .compared_algorithms.de_family.de import DEOptimizer
from .compared_algorithms.de_family.jade import JADEOptimizer
from .compared_algorithms.de_family.lshade import LSHADEOptimizer
from .compared_algorithms.de_family.ilshade_rsp import ILSHADERSPOptimizer
from .compared_algorithms.de_family.qgdecc import QGDECCOptimizer
from .compared_algorithms.esa_family.cma_es import CMAESOptimizer
from .compared_algorithms.esa_family.lr_cma_es import LRCMAESOptimizer
from .compared_algorithms.swarm_family.pso import PSOOptimizer
from .compared_algorithms.swarm_family.gwo import GWOOptimizer
from .compared_algorithms.swarm_family.hho import HHOOptimizer
from .compared_algorithms.swarm_family.sma import SMAOptimizer
from .compared_algorithms.physics_family.rime import RIMEOptimizer
from .compared_algorithms.physics_family.mirime import MIRIMEOptimizer

# ------------------------------------------------- shdms-abc suite bridge ---

_SUITE_DIR = Path(__file__).resolve().parent / "shdms-abc"


def _load_hyphen_layer(layer: str, alias: str):
    """Load ``algorithm/shdms-abc/<layer>`` as ``shdms_abc_suite.<alias>``."""
    pkg_name = "shdms_abc_suite.%s" % alias
    if pkg_name in sys.modules:
        return sys.modules[pkg_name]
    spec = importlib.util.spec_from_file_location(
        pkg_name,
        _SUITE_DIR / layer / "__init__.py",
        submodule_search_locations=[str(_SUITE_DIR / layer)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[pkg_name] = module
    spec.loader.exec_module(module)
    return module


# Register a lightweight parent so relative imports inside the suite resolve.
if "shdms_abc_suite" not in sys.modules:
    _parent_spec = importlib.util.spec_from_file_location(
        "shdms_abc_suite", _SUITE_DIR / "__init__.py"
    )
    _parent = importlib.util.module_from_spec(_parent_spec)
    sys.modules["shdms_abc_suite"] = _parent
    _parent_spec.loader.exec_module(_parent)

_modeling = _load_hyphen_layer("modeling", "modeling")
_optimizer = _load_hyphen_layer("optimizer", "optimizer")

# The registry imports ``run_shdms_abc`` from the alias package; the bridge
# above has already registered it, so this import is now safe.
from .registry import algorithm_display_names, all_algorithm_names, optimize_algorithm  # noqa: E402

from shdms_abc_suite.optimizer.shdms_abc import (  # noqa: E402
    CycleMetrics,
    SHDMSABCConfig,
    SHDMSABCResult,
    SHDMSArtificialBeeColony,
    run_shdms_abc,
)

__all__ = [
    "AlgorithmResult",
    "Bounds",
    "GenericConfig",
    "ObjectiveFunction",
    "Vector",
    "StandardABC",
    "GbestABC",
    "MeABC",
    "MABC",
    "IABC",
    "PSOOptimizer",
    "DEOptimizer",
    "JADEOptimizer",
    "LSHADEOptimizer",
    "CMAESOptimizer",
    "GWOOptimizer",
    "HHOOptimizer",
    "ILSHADERSPOptimizer",
    "SMAOptimizer",
    "RIMEOptimizer",
    "QGDECCOptimizer",
    "MIRIMEOptimizer",
    "LRCMAESOptimizer",
    "CycleMetrics",
    "SHDMSABCConfig",
    "SHDMSABCResult",
    "SHDMSArtificialBeeColony",
    "run_shdms_abc",
    "optimize_algorithm",
    "algorithm_display_names",
    "all_algorithm_names",
]
