"""Schema validation plus consistency rules, combined into one report."""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys

from .rules import ERROR, Report, check

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "schema", "coa.schema.json")


def load_schema(path: str | None = None) -> dict:
    with open(path or SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def schema_errors(doc: dict, schema: dict | None = None) -> list[str]:
    """Validate against the JSON Schema.

    Hard-stops when jsonschema is missing rather than silently skipping. A validator
    that reports "no schema errors" because it could not check is worse than one that
    refuses to run.
    """
    try:
        import jsonschema
    except ImportError:
        sys.exit(
            "coa-validate requires the 'jsonschema' package for schema validation.\n"
            "  pip install jsonschema\n"
            "Refusing to continue: reporting a clean result without having checked "
            "would be a false negative."
        )
    validator = jsonschema.Draft202012Validator(schema or load_schema())
    out = []
    for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        loc = ".".join(str(p) for p in e.absolute_path) or "(root)"
        out.append(f"{loc}: {e.message}")
    return out


def run(doc: dict, as_of: _dt.date | None = None,
        max_age_days: int | None = None,
        schema: dict | None = None) -> Report:
    """Full validation. Schema errors are folded in as ERROR findings."""
    report = Report()
    for msg in schema_errors(doc, schema):
        path, _, detail = msg.partition(": ")
        report.add("SCHEMA", ERROR, detail or msg, path)
    consistency = check(doc, as_of=as_of, max_age_days=max_age_days)
    report.findings.extend(consistency.findings)
    return report


def run_file(path: str, **kw) -> Report:
    with open(path, encoding="utf-8") as fh:
        try:
            doc = json.load(fh)
        except json.JSONDecodeError as e:
            r = Report()
            r.add("PARSE", ERROR, f"not valid JSON: {e}", path)
            return r
    return run(doc, **kw)
