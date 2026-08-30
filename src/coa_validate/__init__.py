"""Validate certificates of analysis against a published schema and a set of
self-consistency rules.

    from coa_validate import validate
    report = validate.run(document)
"""
from . import rules, validate  # noqa: F401

__version__ = "1.0.0"
__all__ = ["rules", "validate"]
