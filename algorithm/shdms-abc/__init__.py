"""SHDMS-ABC suite: railway modeling layer + optimizer layer.

Layout
------
modeling/  joint headway-dwell optimization model (Sections 3.1.1-3.1.4)
optimizer/ Success-History Driven Dynamic Multi-Strategy ABC (Section 3.2)

This directory name contains a hyphen, so it is NOT importable as a Python
package. ``algorithm/__init__.py`` loads both layers explicitly via importlib
and registers the alias module ``shdms_abc_suite`` for internal use.
"""
