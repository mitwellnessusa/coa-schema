# COA Schema

A JSON Schema for certificates of analysis, and a validator that checks a certificate
against itself.

Certificates of analysis are published as PDFs designed for human reading. That makes them
hard to compare across laboratories, hard to check in bulk, and easy to publish with
defects nobody notices. This repository defines a machine-readable representation of what
a certificate states, and a validator that catches the defects.

The validator does two separate things:

1. **Schema validation** — is the document well-formed?
2. **Consistency rules** — does the certificate contradict itself, and can a reader
   actually use it?

The second is where real defects surface. A certificate can be perfectly well-formed and
still report a result that violates its own acceptance criterion while marked as passing.

## Install

```bash
pip install coa-validate
```

Or from source:

```bash
git clone https://github.com/mitwellnessusa/coa-schema
cd coa-schema
pip install -e .
```

## Use

```bash
coa-validate examples/valid-botanical.coa.json
coa-validate lots/*.json --max-age-days 365 --json
```

```python
from coa_validate.validate import run

report = run(document, max_age_days=365)
for finding in report.findings:
    print(finding)
print(report.ok)
```

Exit status is 0 when no file produced an error and 1 otherwise, so it drops into CI
without wrapping.

## What it catches

```
ERROR   R046 [results[0] Lead]: outcome states 'pass' but 4.2 mg/kg against
        specification <= 1.0 mg/kg does not conform. The certificate contradicts itself.
ERROR   R001 [product.lot_identifier]: lot identifier is a placeholder. A certificate
        that cannot be matched to a lot in hand is decorative.
ERROR   R022 [laboratory.accreditation[0]]: accreditation ISO/IEC 17025:2017 expired
        2025-01-01, before testing on 2026-04-05.
ERROR   R010 [document.date_issued]: document.date_issued (2026-01-15) precedes
        sampling.date_tested (2026-02-10); the sequence is impossible.
WARNING R051 [results]: heavy metals panel omits cadmium, mercury.
```

Units are converted before comparison. A result of 900 ppb against a limit of
1.5 mg/kg conforms, because 900 ppb is 0.9 mg/kg — a validator comparing raw numbers
would report a contradiction that does not exist. When two units are genuinely not
comparable, the validator says so rather than guessing a verdict.

The full rule list is in [the documentation](https://coa-schema.readthedocs.io/).

## Scope

This schema describes **what a certificate states**. It does not and cannot assert that a
stated result is correct, that a laboratory is competent, or that a product is safe.
A certificate that passes every rule here is internally consistent and readable. That is
all the validator claims.

Acceptance criteria vary by jurisdiction, product category and monograph. The schema
records the criterion a certificate was judged against and checks the judgement for
self-consistency; it does not supply criteria of its own.

## Structure

```
schema/coa.schema.json    the schema (JSON Schema draft 2020-12)
src/coa_validate/         validator: rules.py has no dependencies
examples/                 one valid certificate, four with deliberate defects
tests/                    27 tests, runnable without pytest
docs/                     built by Read the Docs
```

Run the tests directly:

```bash
python3 tests/test_validate.py
```

## Contributing

Additional rules are welcome, particularly for product categories not represented in the
examples. A rule should describe a defect that makes a certificate self-contradictory or
unusable — not a preference about how certificates ought to look.

Open an issue before a large change.

## Maintenance and disclosure

This repository is maintained by MitWellness, a botanical manufacturer that publishes
lot-level certificates of analysis at
[mitwellness.com/pages/coas](https://www.mitwellness.com/pages/coas). The schema was
written for internal use and released because the problem is not specific to one company.

Nothing here is specific to any manufacturer or product line, and no rule advantages one.
If any part of the schema reads as though it does, that is a defect — please open an issue.

## License

MIT. See [LICENSE](LICENSE).
