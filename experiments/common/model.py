"""Compatibility access to the canonical joint headway--dwell model.

All experiment and preprocessing scripts historically import ``common.model``.
The implementation now lives in
``Joint_Headway_Dwell_Opt.joint_headway_dwell_model`` so that manuscript
Sections 3.1.1--3.1.4 have one authoritative, directly reusable code module.
"""

from Joint_Headway_Dwell_Opt.joint_headway_dwell_model import *
from Joint_Headway_Dwell_Opt.joint_headway_dwell_model import __all__
