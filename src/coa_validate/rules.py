"""Consistency rules for certificates of analysis.

Schema validation answers "is this well-formed?". These rules answer the more useful
question: "does this certificate contradict itself, and can a reader actually use it?"

Every rule is pure Python with no dependencies, so the rule engine runs even where
jsonschema is unavailable. Each returns zero or more Finding objects.

Severity:
    ERROR    the certificate contradicts itself, or omits something that makes it
             unusable for its stated purpose
    WARNING  usable but materially weaker than it should be
    INFO     worth a reader's attention, not a defect
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import Any

ERROR, WARNING, INFO = "ERROR", "WARNING", "INFO"

# Units expressing a mass fraction, and their factor to mg/kg.
# ppm and mg/kg are equal; ppb is one thousandth of ppm. Confusing those two is a
# 1000x error and it appears in real certificates.
_MASS_FRACTION = {
    "mg/kg": 1.0, "ppm": 1.0, "ug/g": 1.0,
    "ug/kg": 0.001, "ppb": 0.001,
    "mg/g": 1000.0,
    "percent": 10000.0,
}

_PLACEHOLDERS = {"", "-", "--", "n/a", "na", "none", "null", "tbd", "unknown",
                 "not applicable", "xxx", "test", "sample"}

_HEAVY_METALS = {"lead", "arsenic", "cadmium", "mercury"}

# Pathogens are presence/absence questions, not quantities.
_PATHOGENS = {"salmonella", "escherichia coli", "e. coli", "e coli",
              "listeria", "listeria monocytogenes", "staphylococcus aureus"}


@dataclass
class Finding:
    rule: str
    severity: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        loc = f" [{self.path}]" if self.path else ""
        return f"{self.severity:<7} {self.rule}{loc}: {self.message}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, *a, **kw) -> None:
        self.findings.append(Finding(*a, **kw))

    def of(self, severity: str) -> list[Finding]:
        return [f for f in self.findings if f.severity == severity]

    @property
    def ok(self) -> bool:
        return not self.of(ERROR)


def _date(value: Any) -> _dt.date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return _dt.date.fromisoformat(value)
    except ValueError:
        return None


def _to_mgkg(value: float, unit: str | None) -> float | None:
    """Convert to mg/kg, or None when the unit is not a mass fraction."""
    if unit is None:
        return None
    factor = _MASS_FRACTION.get(unit)
    return None if factor is None else value * factor


def _label(result: dict, index: int) -> str:
    return f"results[{index}] {result.get('analyte', '?')}"


# --------------------------------------------------------------------- rules

def check(doc: dict, as_of: _dt.date | None = None,
          max_age_days: int | None = None) -> Report:
    """Run every consistency rule against a parsed certificate."""
    rep = Report()
    _check_identity(doc, rep)
    _check_dates(doc, rep, as_of)
    _check_laboratory(doc, rep)
    _check_results(doc, rep)
    _check_panels(doc, rep)
    _check_age(doc, rep, as_of, max_age_days)
    return rep


def _check_identity(doc: dict, rep: Report) -> None:
    product = doc.get("product") or {}
    lot = (product.get("lot_identifier") or "").strip()
    if lot.lower() in _PLACEHOLDERS:
        rep.add("R001", ERROR,
                "lot identifier is a placeholder. A certificate that cannot be matched "
                "to a lot in hand is decorative.",
                "product.lot_identifier")

    document = doc.get("document") or {}
    if (document.get("document_id") or "").strip().lower() in _PLACEHOLDERS:
        rep.add("R002", ERROR, "document identifier is a placeholder.",
                "document.document_id")

    if document.get("supersedes") and not document.get("revision"):
        rep.add("R003", WARNING,
                "certificate supersedes another but carries no revision number.",
                "document.revision")


def _check_dates(doc: dict, rep: Report, as_of: _dt.date | None) -> None:
    product = doc.get("product") or {}
    sampling = doc.get("sampling") or {}
    document = doc.get("document") or {}

    seq = [
        ("product.date_manufactured", _date(product.get("date_manufactured"))),
        ("sampling.date_received", _date(sampling.get("date_received"))),
        ("sampling.date_tested", _date(sampling.get("date_tested"))),
        ("document.date_issued", _date(document.get("date_issued"))),
    ]
    known = [(name, d) for name, d in seq if d is not None]
    for (n1, d1), (n2, d2) in zip(known, known[1:]):
        if d2 < d1:
            rep.add("R010", ERROR,
                    f"{n2} ({d2}) precedes {n1} ({d1}); the sequence is impossible.",
                    n2)

    horizon = as_of or _dt.date.today()
    for name, d in known:
        if d > horizon:
            rep.add("R011", ERROR, f"{name} ({d}) is in the future.", name)

    if not _date(sampling.get("date_tested")):
        rep.add("R012", WARNING,
                "no test date. Only the issue date is known, so the result cannot be "
                "placed relative to manufacture.",
                "sampling.date_tested")


def _check_laboratory(doc: dict, rep: Report) -> None:
    lab = doc.get("laboratory") or {}
    if (lab.get("name") or "").strip().lower() in _PLACEHOLDERS:
        rep.add("R020", ERROR, "laboratory is unnamed; the result is unverifiable.",
                "laboratory.name")

    if lab.get("independent") is False:
        rep.add("R021", INFO,
                "laboratory is declared non-independent. Reportable, not a defect, "
                "but a reader should know.",
                "laboratory.independent")

    tested = _date((doc.get("sampling") or {}).get("date_tested"))
    for i, acc in enumerate(lab.get("accreditation") or []):
        expires = _date(acc.get("expires"))
        if expires and tested and expires < tested:
            rep.add("R022", ERROR,
                    f"accreditation {acc.get('standard')} expired {expires}, before "
                    f"testing on {tested}.",
                    f"laboratory.accreditation[{i}]")

    if not lab.get("accreditation"):
        rep.add("R023", WARNING,
                "no accreditation stated. ISO/IEC 17025 is the usual claim; its absence "
                "is not proof of a problem but it is unverifiable competence.",
                "laboratory.accreditation")


def _check_results(doc: dict, rep: Report) -> None:
    for i, r in enumerate(doc.get("results") or []):
        where = _label(r, i)
        value = r.get("value")
        qualifier = r.get("value_qualifier")

        if value is None and qualifier is None:
            rep.add("R030", ERROR,
                    "result carries neither a value nor a qualifier; it asserts nothing.",
                    where)

        if value is not None and r.get("unit") is None:
            rep.add("R031", ERROR, "numeric result with no unit.", where)

        loq = r.get("limit_of_quantitation")
        lod = r.get("limit_of_detection")
        if loq is not None and lod is not None and lod > loq:
            rep.add("R032", ERROR,
                    f"limit of detection ({lod}) exceeds limit of quantitation ({loq}).",
                    where)

        if value is not None and loq is not None and value < loq:
            rep.add("R033", WARNING,
                    f"value {value} is below the stated limit of quantitation ({loq}). "
                    "Report it as below_loq rather than as a number.",
                    where)

        _check_outcome(r, where, rep)


def _check_outcome(r: dict, where: str, rep: Report) -> None:
    spec = r.get("specification") or {}
    outcome = r.get("outcome")
    op = spec.get("operator")
    if not spec:
        if outcome in ("pass", "fail"):
            rep.add("R040", ERROR,
                    f"outcome '{outcome}' with no specification. Nothing was compared.",
                    where)
        return

    if op == "range":
        if spec.get("min") is None or spec.get("max") is None:
            rep.add("R041", ERROR, "range specification needs both min and max.", where)
            return
        if spec["min"] > spec["max"]:
            rep.add("R042", ERROR,
                    f"specification min ({spec['min']}) exceeds max ({spec['max']}).",
                    where)
            return
    elif op in ("<=", "<", ">=", ">", "==") and spec.get("value") is None:
        rep.add("R043", ERROR, f"'{op}' specification needs a value.", where)
        return

    value = r.get("value")
    if value is None:
        # Non-numeric results can still be judged, e.g. absent_in for a pathogen.
        if op == "absent_in" and r.get("value_qualifier") == "detected" \
                and outcome == "pass":
            rep.add("R044", ERROR,
                    "analyte detected against an absence specification, marked pass.",
                    where)
        return

    r_unit, s_unit = r.get("unit"), spec.get("unit")
    if s_unit and r_unit and s_unit != r_unit:
        if r_unit not in _MASS_FRACTION or s_unit not in _MASS_FRACTION:
            rep.add("R045", ERROR,
                    f"result is in {r_unit} but the specification is in {s_unit}; "
                    "the two are not comparable.",
                    where)
            return
        value_cmp = _to_mgkg(value, r_unit)
        bounds = {k: _to_mgkg(v, s_unit)
                  for k, v in (("value", spec.get("value")),
                               ("min", spec.get("min")),
                               ("max", spec.get("max"))) if v is not None}
    else:
        value_cmp = value
        bounds = {k: v for k, v in (("value", spec.get("value")),
                                    ("min", spec.get("min")),
                                    ("max", spec.get("max"))) if v is not None}

    conforms = _conforms(value_cmp, op, bounds)
    if conforms is None or outcome not in ("pass", "fail"):
        return

    stated = outcome == "pass"
    if stated != conforms:
        spec_text = _spec_text(op, spec)
        rep.add("R046", ERROR,
                f"outcome states '{outcome}' but {value} {r.get('unit') or ''}".rstrip()
                + f" against specification {spec_text} "
                + ("conforms" if conforms else "does not conform")
                + ". The certificate contradicts itself.",
                where)


def _conforms(value: float, op: str, b: dict) -> bool | None:
    if op == "<=" and "value" in b:
        return value <= b["value"]
    if op == "<" and "value" in b:
        return value < b["value"]
    if op == ">=" and "value" in b:
        return value >= b["value"]
    if op == ">" and "value" in b:
        return value > b["value"]
    if op == "==" and "value" in b:
        return value == b["value"]
    if op == "range" and "min" in b and "max" in b:
        return b["min"] <= value <= b["max"]
    return None


def _spec_text(op: str, spec: dict) -> str:
    unit = spec.get("unit") or ""
    if op == "range":
        return f"{spec.get('min')}-{spec.get('max')} {unit}".strip()
    return f"{op} {spec.get('value')} {unit}".strip()


def _check_panels(doc: dict, rep: Report) -> None:
    results = doc.get("results") or []

    seen: dict[tuple[str, str], int] = {}
    for i, r in enumerate(results):
        key = ((r.get("analyte") or "").strip().lower(), r.get("panel") or "")
        if key in seen:
            rep.add("R050", WARNING,
                    f"'{r.get('analyte')}' appears more than once in the "
                    f"{r.get('panel')} panel (also at index {seen[key]}).",
                    _label(r, i))
        seen[key] = i

    hm = {(r.get("analyte") or "").strip().lower()
          for r in results if r.get("panel") == "heavy_metals"}
    if hm:
        missing = sorted(_HEAVY_METALS - hm)
        if missing:
            rep.add("R051", WARNING,
                    "heavy metals panel omits " + ", ".join(missing)
                    + ". The four commonly reported elements are lead, arsenic, "
                      "cadmium and mercury.",
                    "results")

    for i, r in enumerate(results):
        name = (r.get("analyte") or "").strip().lower()
        if r.get("panel") == "microbial" and name in _PATHOGENS:
            if r.get("value") is not None and r.get("value_qualifier") is None:
                rep.add("R052", WARNING,
                        f"'{r.get('analyte')}' is a presence/absence determination; "
                        "a count is the wrong representation.",
                        _label(r, i))


def _check_age(doc: dict, rep: Report, as_of: _dt.date | None,
               max_age_days: int | None) -> None:
    if max_age_days is None:
        return
    issued = _date((doc.get("document") or {}).get("date_issued"))
    if not issued:
        return
    age = ((as_of or _dt.date.today()) - issued).days
    if age > max_age_days:
        rep.add("R060", WARNING,
                f"certificate is {age} days old, beyond the {max_age_days}-day "
                "threshold given.",
                "document.date_issued")
