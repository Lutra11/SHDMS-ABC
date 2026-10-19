"""Compatibility access to the canonical joint headway--dwell model.

All experiment and preprocessing scripts historically import ``common.model``.
The implementation lives in the SHDMS-ABC modeling layer
(``algorithm/shdms-abc/modeling/joint_headway_dwell_model.py``) so that
manuscript Sections 3.1.1--3.1.4 have one authoritative, directly reusable
code module.

The ``shdms-abc`` folder carries a hyphen in its name and is therefore not a
Python package. ``algorithm/__init__.py`` bridges its layers into the alias
package ``shdms_abc_suite``. This shim makes sure the repository root is
importable and the bridge is loaded before re-exporting the model API, no
matter which module imports ``common`` first.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]  # .../github-content
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import algorithm  # noqa: F401  (loads the shdms_abc_suite alias bridge)

from shdms_abc_suite.modeling import *  # noqa: E402,F403
from shdms_abc_suite.modeling import __all__  # noqa: E402,F401
