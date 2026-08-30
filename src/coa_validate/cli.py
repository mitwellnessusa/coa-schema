"""Command line entry point.

    coa-validate examples/valid-botanical.coa.json
    coa-validate lots/*.json --max-age-days 365 --json
    python3 -m coa_validate.cli <file>

Exit status is 0 when no file produced an ERROR, 1 otherwise, so it drops into CI
without wrapping.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import sys

from .rules import ERROR, INFO, WARNING
from .validate import load_schema, run_file


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except BrokenPipeError:
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="coa-validate",
        description="Validate certificates of analysis for well-formedness and "
                    "self-consistency.")
    ap.add_argument("files", nargs="+", help="COA JSON files, globs accepted")
    ap.add_argument("--schema", help="path to an alternate schema")
    ap.add_argument("--as-of", help="evaluate dates against this date (YYYY-MM-DD)")
    ap.add_argument("--max-age-days", type=int,
                    help="warn when a certificate is older than this")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="errors only")
    a = ap.parse_args(argv)

    as_of = _dt.date.fromisoformat(a.as_of) if a.as_of else None
    schema = load_schema(a.schema) if a.schema else None

    paths: list[str] = []
    for pattern in a.files:
        hits = sorted(glob.glob(pattern))
        paths.extend(hits or [pattern])

    payload, failed = [], 0
    for path in paths:
        rep = run_file(path, as_of=as_of, max_age_days=a.max_age_days, schema=schema)
        errs, warns = rep.of(ERROR), rep.of(WARNING)
        if errs:
            failed += 1

        if a.json:
            payload.append({
                "file": path, "ok": rep.ok,
                "findings": [f.__dict__ for f in rep.findings],
            })
            continue

        status = "FAIL" if errs else ("PASS" if not warns else "PASS with warnings")
        print(f"\n{path}\n  {status} — {len(errs)} error(s), {len(warns)} warning(s)")
        for f in rep.findings:
            if a.quiet and f.severity != ERROR:
                continue
            print("  " + str(f))

    if a.json:
        print(json.dumps({"files": len(paths), "failed": failed,
                          "results": payload}, indent=2))
    else:
        print(f"\n{len(paths)} file(s), {failed} with errors.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
