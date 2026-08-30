# COA Schema

A JSON Schema for certificates of analysis, and a validator that checks a certificate
against itself.

## What problem this solves

Certificates of analysis are published as PDFs built for human reading. That makes them
hard to compare across laboratories, hard to check in bulk, and easy to publish with
defects nobody notices.

A certificate can be perfectly well-formed and still report a result that violates its own
acceptance criterion while marked as passing. No PDF viewer will tell you that. This
validator will.

## The two layers

**Schema validation** answers whether the document is well-formed: required fields present,
dates in ISO 8601, units drawn from a closed list, at least one result.

**Consistency rules** answer the more useful question: does the certificate contradict
itself, and can a reader use it? A result that exceeds its own limit but is marked pass.
A test date after the issue date. An accreditation that expired before testing. A lot
identifier reading "N/A".

The rules have no dependencies, so they run anywhere Python does.

## What it does not do

This schema describes what a certificate *states*. It does not assert that a stated result
is correct, that a laboratory is competent, or that a product is safe.

A certificate that passes every rule is internally consistent and readable. That is the
whole claim.

Acceptance criteria vary by jurisdiction, product category and monograph. The schema
records the criterion a certificate was judged against and checks the judgement for
self-consistency. It does not supply criteria of its own, and adding a table of "correct"
limits would be wrong — the correct limit depends on the product and the market.

## Start here

- [Reading a certificate](reading-a-coa.md) — what the fields mean and which ones matter
- [Field reference](fields.md) — every field in the schema
- [Validation rules](rules.md) — every rule, what it catches and why
- [Using the validator](usage.md) — CLI and Python

## License

MIT.
