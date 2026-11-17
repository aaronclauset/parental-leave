"""The statutory leave floor of a record's jurisdiction (rule U7; the record field `statutory_floor`).

Read from the `floor_2018_*` columns of reference/statutory_baseline.csv by the institution's jurisdiction
(reference/institutions.csv): U.S. institutions take the federal FMLA row, Canadian institutions their province's.
The floor is filled by code, never by a reader; every released record carries the value floor_for() returns, which
code/test_rebuild.py checks.

Usage (from the version folder, data/2018/v2.0/): python code/statutory_floor.py    # prints any record whose floor differs

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "reference" / "statutory_baseline.csv"
INSTITUTIONS = ROOT / "reference" / "institutions.csv"
YEAR = "2018"


def citation(text):
    """The legal citation without the trailing list of saved-text document ids, e.g. '(2026_00, 2026_01)'."""
    return re.sub(r"\s*\([^()]*\b\d{4}_\d\d[^()]*\)\s*$", "", text)


def floors():
    out = {}
    with open(TABLE, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get(f"floor_{YEAR}_weeks_birth"):
                out[r["jurisdiction"]] = {
                    "weeks_birth": float(r[f"floor_{YEAR}_weeks_birth"]),
                    "weeks_nonbirth": float(r[f"floor_{YEAR}_weeks_nonbirth"]),
                    "statute": f"{r['provision']} ({citation(r['source_citation'])})",
                    "source_doc": r[f"floor_{YEAR}_source_doc"]}
    return out


def jurisdictions():
    with open(INSTITUTIONS, encoding="utf-8") as f:
        return {r["institution_id"]: r for r in csv.DictReader(f)}


def floor_for(rec, table=None, juris=None):
    """The statutory_floor object for this record, or None if the table has no row for its jurisdiction."""
    table = table if table is not None else floors()
    juris = juris if juris is not None else jurisdictions()
    j = juris.get(rec["slug"])
    if not j:
        return None
    key = "US" if j["country"] == "US" else j["state_province"]
    row = table.get(key)
    if not row:
        return None
    return {"jurisdiction": key, "year": YEAR, **row, "table": "statutory_baseline.csv"}


def main():
    table, juris = floors(), jurisdictions()
    bad = 0
    for p in sorted((ROOT / "records").glob("*.json")):
        with open(p, encoding="utf-8") as f:
            rec = json.load(f)
        if rec.get("statutory_floor") != floor_for(rec, table, juris):
            bad += 1
            print(f"{rec['slug']}: statutory_floor differs from the table")
    print(f"{bad} records differ")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
