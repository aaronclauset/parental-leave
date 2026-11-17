"""Parse a component's free-text `pay_fraction` into `pay_fraction_pct` (rule R15b).

    pct(text) -> int | None

The number is the pay the employee receives during the period as a percentage of normal pay (gross: a top-up
"to 95% integrated with EI" is 95). Plain-English forms of full pay ("with pay", "full salary", "no reduction
in pay", "regular rate of pay") are 100; "one-half" is 50; "two-thirds" 67. Text that states no level
("paid (rate not stated)", "" ) gives None, and the field is filled by hand or left empty.

Usage (report what parses; paths relative to the version folder, data/2018/v2.0/): python code/pay_fraction.py records

The rules cited by id are defined in guidance/rules.md.

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""

import glob
import json
import re
import sys
from pathlib import Path

_NUM = r"(\d{1,3}(?:\.\d+)?)\s*(?:%|percent|per cent)"
_FULL = (r"\bfull(?:[- ](?:pay|salary|compensation|regular pay|base salary|time pay)|y[- ]paid)\b|\bat full\b|"
         r"\bregular (?:base )?(?:rate of )?(?:pay|salary|monthly salary)\b|\bnormal (?:pay|salary)\b|"
         r"\b(?:no|without(?: a)?) (?:reduction|loss) (?:in|of) (?:pay|salary|compensation)\b|\bsame salary\b|"
         r"\bsalar(?:y|ies)[^.]{0,40}not be affected\b|\b(?:approved |her |his )?base (?:monthly )?salary\b|\bregular employer salary\b|\bsalary and benefits\b|\bavec traitement\b|\bplein traitement\b|\b100 ?% of\b")
_PATTERNS = [
    (re.compile(r"\b(?:up to|to a maximum of|equal to|amounts? to|totals?)\s*" + _NUM, re.I), lambda m: float(m.group(1))),
    (re.compile(_NUM, re.I), lambda m: float(m.group(1))),
    (re.compile(_FULL, re.I), lambda m: 100.0),
    (re.compile(r"\bone[- ]half\b|\bhalf(?:[- ](?:pay|salary|time|of))\b", re.I), lambda m: 50.0),
    (re.compile(r"\btwo[- ]thirds\b", re.I), lambda m: 67.0),
    (re.compile(r"\bwith pay\b|\bpaid\b(?!\s+(?:at|through|by|from|via|in)\b)(?![^.]{0,30}not stated)", re.I), lambda m: 100.0),
]
_NOT_STATED = re.compile(r"not stated|rate not|level not|unstated|unknown|unpaid|no salary|without pay|none", re.I)


def pct(text):
    """Percentage of normal pay stated in the text, or None when it states no level."""
    if not text:
        return None
    t = str(text).strip()
    if _NOT_STATED.search(t) and not re.search(_NUM, t, re.I):
        return None
    for rx, f in _PATTERNS:
        m = rx.search(t)
        if m:
            v = f(m)
            return int(v) if 0 < v <= 100 else None
    return None


def main(records_dir):
    n = hit = 0
    for p in sorted(glob.glob(str(Path(records_dir) / "*.json"))):
        r = json.load(open(p, encoding="utf-8"))
        for c in r["components"]:
            if "pay_fraction" in c:
                n += 1
                v = c.get("pay_fraction_pct")
                if v is None:
                    v = pct(c["pay_fraction"])
                if v is not None:
                    hit += 1
                else:
                    print(f"  unparsed  {r['slug']:36s} {c['component_id']:36s} {c['pay_fraction']!r:.80}")
    print(f"{hit}/{n} components with pay_fraction have a pay level")


if __name__ == "__main__":
    main(sys.argv[1])
