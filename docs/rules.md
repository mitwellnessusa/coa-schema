# Validation rules

Schema errors are reported with the rule id `SCHEMA`. Everything else comes from
`coa_validate.rules`, which has no dependencies.

**Severity**

| Level | Meaning | Effect on exit status |
| --- | --- | --- |
| ERROR | The certificate contradicts itself, or omits something that makes it unusable | Non-zero |
| WARNING | Usable, but materially weaker than it should be | None |
| INFO | Worth a reader's attention, not a defect | None |

## Identity

| Rule | Severity | Catches |
| --- | --- | --- |
| R001 | ERROR | Lot identifier is a placeholder — `N/A`, `TBD`, `-`, blank |
| R002 | ERROR | Document identifier is a placeholder |
| R003 | WARNING | Certificate supersedes another but carries no revision number |

## Dates

| Rule | Severity | Catches |
| --- | --- | --- |
| R010 | ERROR | Impossible ordering: manufactured, received, tested, issued must not run backwards |
| R011 | ERROR | A date in the future |
| R012 | WARNING | No test date, so the result cannot be placed relative to manufacture |
| R060 | WARNING | Certificate older than the `--max-age-days` threshold given |

## Laboratory

| Rule | Severity | Catches |
| --- | --- | --- |
| R020 | ERROR | Laboratory unnamed; every result is unverifiable |
| R021 | INFO | Laboratory declared non-independent |
| R022 | ERROR | Accreditation expired before the testing date |
| R023 | WARNING | No accreditation stated |

R021 is informational by design. A manufacturer testing in its own laboratory is
reportable, not a defect, and the schema records it rather than judging it.

## Results

| Rule | Severity | Catches |
| --- | --- | --- |
| R030 | ERROR | Result with neither a value nor a qualifier — it asserts nothing |
| R031 | ERROR | Numeric result with no unit |
| R032 | ERROR | Limit of detection exceeds limit of quantitation, which is impossible |
| R033 | WARNING | A numeric value below the stated limit of quantitation |

## Outcome against specification

The rules that catch the most real defects.

| Rule | Severity | Catches |
| --- | --- | --- |
| R040 | ERROR | Outcome of pass or fail with no specification — nothing was compared |
| R041 | ERROR | Range specification missing min or max |
| R042 | ERROR | Specification min exceeds max |
| R043 | ERROR | Comparison specification with no value |
| R044 | ERROR | Analyte detected against an absence criterion, marked pass |
| R045 | ERROR | Result and specification in units that cannot be compared |
| R046 | ERROR | Stated outcome contradicts the comparison |

R046 fires in both directions. A result exceeding its limit but marked pass is the obvious
case; a conforming result marked fail is equally a contradiction and equally reported.

R045 exists so the validator never guesses. CFU/g cannot be compared to mg/kg, so the
validator says so instead of producing a verdict it cannot compute.

## Panels

| Rule | Severity | Catches |
| --- | --- | --- |
| R050 | WARNING | The same analyte appears twice in one panel |
| R051 | WARNING | Heavy metals panel omits lead, arsenic, cadmium or mercury |
| R052 | WARNING | A pathogen reported as a count rather than presence/absence |

R051 is a warning, not an error. An omission may be deliberate and documented. It is worth
noticing, not worth failing.

## Unit conversion

Mass fraction units are converted to mg/kg before comparison:

| Unit | Factor to mg/kg |
| --- | --- |
| mg/kg, ppm, µg/g | 1 |
| µg/kg, ppb | 0.001 |
| mg/g | 1,000 |
| percent | 10,000 |

Units outside this table — CFU/g, MPN/g, mg/mL, mg/serving — are not mass fractions and
are never converted. Comparing one to a mass fraction raises R045.

## Adding a rule

A rule should describe a defect that makes a certificate self-contradictory or unusable,
not a preference about how certificates ought to look. Add the check to
`src/coa_validate/rules.py` and a test in both directions — one case where it fires and,
where a false positive would be damaging, one where it must stay quiet.
