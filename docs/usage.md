# Using the validator

## Command line

```bash
coa-validate examples/valid-botanical.coa.json
coa-validate lots/*.json
coa-validate lots/*.json --max-age-days 365
coa-validate lots/*.json --json > report.json
coa-validate lots/*.json --quiet          # errors only
coa-validate lots/*.json --as-of 2026-01-01
```

`--as-of` evaluates dates against a fixed date instead of today, which makes results
reproducible in tests and in CI.

Exit status is 0 when no file produced an error and 1 otherwise.

## Python

```python
from coa_validate.validate import run, run_file

report = run_file("lots/EBP-2601-0087.json", max_age_days=365)

if not report.ok:
    for finding in report.of("ERROR"):
        print(finding.rule, finding.path, finding.message)
```

`Report.findings` holds every finding. `Report.of(severity)` filters. `Report.ok` is True
when there are no errors.

To run the consistency rules without schema validation — useful where `jsonschema` is not
available:

```python
from coa_validate.rules import check

report = check(document)
```

## In CI

```yaml
- run: pip install coa-validate
- run: coa-validate coas/*.json --max-age-days 400
```

A failing certificate fails the build. Publishing a certificate that contradicts itself is
worse than publishing none, because it invites a reader to rely on it.

## On missing dependencies

Schema validation requires `jsonschema`. If it is absent the validator exits with an error
rather than skipping the check.

This is deliberate. A validator reporting "no schema errors" because it could not check is
producing a false negative, and a false negative in a quality tool is worse than a crash.
The consistency rules have no dependencies and can always be run directly.
