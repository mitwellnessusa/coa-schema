"""Tests for the consistency rules.

Runnable with pytest, or directly with `python3 tests/test_validate.py` so the repo
can be checked without installing a test runner.

Every rule gets a positive case (it fires when it should) and, where a false positive
would be damaging, a negative case (it stays quiet when it should).
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "src"))

from coa_validate.rules import ERROR, WARNING, check  # noqa: E402
from coa_validate.validate import run  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(os.path.dirname(HERE), "examples")
AS_OF = dt.date(2026, 8, 30)


def load(name):
    with open(os.path.join(EXAMPLES, name), encoding="utf-8") as fh:
        return json.load(fh)


def rules_fired(doc, **kw):
    return {f.rule for f in check(doc, **kw).findings}


def minimal(**over):
    doc = {
        "schema_version": "1.0",
        "document": {"document_id": "D-1", "date_issued": "2026-03-14"},
        "product": {"name": "P", "lot_identifier": "L-1"},
        "laboratory": {"name": "Lab",
                       "accreditation": [{"standard": "ISO/IEC 17025:2017"}]},
        "sampling": {"date_tested": "2026-03-05"},
        "results": [{"analyte": "Lead", "panel": "heavy_metals", "method": "ICP-MS",
                     "value": 0.2, "unit": "mg/kg"}],
    }
    doc.update(over)
    return doc


# ------------------------------------------------------------------ examples

def test_valid_example_is_clean():
    rep = run(load("valid-botanical.coa.json"), as_of=AS_OF)
    assert rep.ok, [str(f) for f in rep.of(ERROR)]
    assert not rep.of(WARNING), [str(f) for f in rep.of(WARNING)]


def test_every_invalid_example_fails():
    for name in sorted(os.listdir(EXAMPLES)):
        if not name.startswith("invalid-"):
            continue
        rep = run(load(name), as_of=AS_OF)
        assert not rep.ok, f"{name} should have produced at least one error"


# ------------------------------------------------------------------ identity

def test_placeholder_lot_is_an_error():
    for placeholder in ("N/A", "  ", "TBD", "-", "unknown"):
        doc = minimal(product={"name": "P", "lot_identifier": placeholder})
        assert "R001" in rules_fired(doc, as_of=AS_OF), placeholder


def test_real_lot_passes():
    assert "R001" not in rules_fired(minimal(), as_of=AS_OF)


# --------------------------------------------------------------------- dates

def test_impossible_date_order():
    doc = minimal(document={"document_id": "D-1", "date_issued": "2026-01-01"},
                  sampling={"date_tested": "2026-02-10"})
    assert "R010" in rules_fired(doc, as_of=AS_OF)


def test_future_date():
    doc = minimal(document={"document_id": "D-1", "date_issued": "2027-01-01"},
                  sampling={"date_tested": "2027-01-01"})
    assert "R011" in rules_fired(doc, as_of=AS_OF)


def test_age_threshold():
    doc = minimal()
    assert "R060" in rules_fired(doc, as_of=AS_OF, max_age_days=30)
    assert "R060" not in rules_fired(doc, as_of=AS_OF, max_age_days=3650)


# ---------------------------------------------------------------- laboratory

def test_expired_accreditation_at_time_of_test():
    doc = minimal(laboratory={"name": "Lab", "accreditation": [
        {"standard": "ISO/IEC 17025:2017", "expires": "2025-01-01"}]})
    assert "R022" in rules_fired(doc, as_of=AS_OF)


def test_accreditation_expiring_after_the_test_is_fine():
    doc = minimal(laboratory={"name": "Lab", "accreditation": [
        {"standard": "ISO/IEC 17025:2017", "expires": "2030-01-01"}]})
    assert "R022" not in rules_fired(doc, as_of=AS_OF)


# ------------------------------------------------------------------- results

def test_result_asserting_nothing():
    doc = minimal(results=[{"analyte": "X", "panel": "other", "method": "m"}])
    assert "R030" in rules_fired(doc, as_of=AS_OF)


def test_lod_above_loq_is_impossible():
    doc = minimal(results=[{"analyte": "Lead", "panel": "heavy_metals",
                            "method": "ICP-MS", "value": 0.1, "unit": "mg/kg",
                            "limit_of_detection": 0.5,
                            "limit_of_quantitation": 0.05}])
    assert "R032" in rules_fired(doc, as_of=AS_OF)


def test_value_below_loq_should_be_qualified():
    doc = minimal(results=[{"analyte": "Lead", "panel": "heavy_metals",
                            "method": "ICP-MS", "value": 0.01, "unit": "mg/kg",
                            "limit_of_quantitation": 0.05}])
    assert "R033" in rules_fired(doc, as_of=AS_OF)


# ------------------------------------------------- outcome vs specification

def _one(**over):
    r = {"analyte": "Lead", "panel": "heavy_metals", "method": "ICP-MS"}
    r.update(over)
    return minimal(results=[r])


def test_pass_that_violates_its_own_spec():
    doc = _one(value=4.2, unit="mg/kg", outcome="pass",
               specification={"operator": "<=", "value": 1.0, "unit": "mg/kg"})
    assert "R046" in rules_fired(doc, as_of=AS_OF)


def test_fail_that_actually_conforms():
    doc = _one(value=0.2, unit="mg/kg", outcome="fail",
               specification={"operator": "<=", "value": 1.0, "unit": "mg/kg"})
    assert "R046" in rules_fired(doc, as_of=AS_OF)


def test_correct_pass_is_quiet():
    doc = _one(value=0.2, unit="mg/kg", outcome="pass",
               specification={"operator": "<=", "value": 1.0, "unit": "mg/kg"})
    assert "R046" not in rules_fired(doc, as_of=AS_OF)


def test_range_specification():
    ok = _one(value=32.4, unit="percent", outcome="pass",
              specification={"operator": "range", "min": 30, "max": 70,
                             "unit": "percent"})
    assert "R046" not in rules_fired(ok, as_of=AS_OF)
    bad = _one(value=12.0, unit="percent", outcome="pass",
               specification={"operator": "range", "min": 30, "max": 70,
                              "unit": "percent"})
    assert "R046" in rules_fired(bad, as_of=AS_OF)


def test_outcome_without_specification():
    doc = _one(value=0.2, unit="mg/kg", outcome="pass")
    assert "R040" in rules_fired(doc, as_of=AS_OF)


def test_incomplete_range_specification():
    doc = _one(value=1.0, unit="percent", outcome="pass",
               specification={"operator": "range", "min": 30, "unit": "percent"})
    assert "R041" in rules_fired(doc, as_of=AS_OF)


# ----------------------------------------------------------- unit conversion

def test_ppb_against_mgkg_converts_correctly():
    """900 ppb is 0.9 mg/kg, which conforms to <= 1.5 mg/kg.

    A validator that compared the raw numbers would see 900 > 1.5 and report a
    contradiction that does not exist. This false positive is the reason the
    conversion table exists, so it gets its own test.
    """
    doc = _one(value=900, unit="ppb", outcome="pass",
               specification={"operator": "<=", "value": 1.5, "unit": "mg/kg"})
    assert "R046" not in rules_fired(doc, as_of=AS_OF)


def test_ppb_conversion_still_catches_a_real_violation():
    doc = _one(value=9000, unit="ppb", outcome="pass",
               specification={"operator": "<=", "value": 1.5, "unit": "mg/kg"})
    assert "R046" in rules_fired(doc, as_of=AS_OF)


def test_percent_against_mgkg():
    # 0.5 percent is 5000 mg/kg, far above a 1 mg/kg limit
    doc = _one(value=0.5, unit="percent", outcome="pass",
               specification={"operator": "<=", "value": 1.0, "unit": "mg/kg"})
    assert "R046" in rules_fired(doc, as_of=AS_OF)


def test_incomparable_units_are_flagged_not_guessed():
    doc = _one(value=100, unit="CFU/g", outcome="pass",
               specification={"operator": "<=", "value": 1.0, "unit": "mg/kg"})
    fired = rules_fired(doc, as_of=AS_OF)
    assert "R045" in fired
    assert "R046" not in fired      # must not guess a verdict it cannot compute


# -------------------------------------------------------------------- panels

def test_pathogen_detected_but_marked_pass():
    doc = minimal(results=[{"analyte": "Salmonella", "panel": "microbial",
                            "method": "USP <2022>", "value_qualifier": "detected",
                            "specification": {"operator": "absent_in"},
                            "outcome": "pass"}])
    assert "R044" in rules_fired(doc, as_of=AS_OF)


def test_pathogen_reported_as_a_count():
    doc = minimal(results=[{"analyte": "Salmonella", "panel": "microbial",
                            "method": "USP <2022>", "value": 0, "unit": "CFU/g"}])
    assert "R052" in rules_fired(doc, as_of=AS_OF)


def test_duplicate_analyte_in_one_panel():
    r = {"analyte": "Lead", "panel": "heavy_metals", "method": "ICP-MS",
         "value": 0.2, "unit": "mg/kg"}
    assert "R050" in rules_fired(minimal(results=[r, dict(r)]), as_of=AS_OF)


def test_incomplete_heavy_metals_panel():
    assert "R051" in rules_fired(minimal(), as_of=AS_OF)


def test_complete_heavy_metals_panel_is_quiet():
    doc = minimal(results=[
        {"analyte": m, "panel": "heavy_metals", "method": "ICP-MS",
         "value": 0.1, "unit": "mg/kg"}
        for m in ("Lead", "Arsenic", "Cadmium", "Mercury")])
    assert "R051" not in rules_fired(doc, as_of=AS_OF)


# ------------------------------------------------------------------- harness

if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"  pass  {name}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {name}: {e}")
        except Exception as e:
            failed += 1
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
    print(f"\n{len(fns)} tests, {failed} failed")
    sys.exit(1 if failed else 0)
