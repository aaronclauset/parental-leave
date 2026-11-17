"""Build the data set CSV from the structured records.

Usage (from the version folder, data/2018/v2.0/):
    python code/build_csv.py [--out parental_leave_2018_v2.0.csv]

Reads records/<institution_id>.json, reference/institutions.csv and reference/component_tiers.csv, derives every
figure with derive.py (guaranteed, and with discretionary provisions), and writes one row per institution, sorted by
institution_id. The columns are described in DATA_DICTIONARY.md; the rules cited are in guidance/rules.md.

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""
import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "parental_leave_2018_v2.0.csv"
RELIEF = {"All duties": "all duties", "Just teaching": "teaching only", "Other": "other", "": ""}
TERM_SOURCE = {"stated": "policy", "calendar": "calendar", "coding_2018": "v1", "kind_default": "default", "": ""}
ROLES = ("birth", "nonbirth")
TIERS = ("primary", "secondary", "tertiary", "contextual")


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def flag_count(rec, prefix):
    """Components carrying at least one flag that starts with prefix."""
    return sum(any(str(f).startswith(prefix) for f in c.get("flags") or []) for c in rec["components"])


def row_for(meta, rec, tiers, terms):
    g = derive.derive(rec, terms, False)  # guaranteed
    d = derive.derive(rec, terms, True)   # with discretionary provisions
    row = {k: meta[k] for k in ("institution", "institution_id", "country", "region", "state_province", "control",
                                "aau_member_2018", "prestige_rank")}
    row["values_available"] = "no" if g["missing"] else "yes"
    for suffix, x in (("", g), ("_disc", d)):
        for role in ROLES:
            row[f"{role}_weeks{suffix}"] = x[f"weeks_2018def_{role}"]
        for role in ROLES:
            row[f"{role}_relief{suffix}"] = RELIEF[x[f"relief_2018def_{role}"]]
        for role in ROLES:
            row[f"{role}_weeks_max{suffix}"] = x[f"weeks_2018def_max_{role}"]
    for name, field, roles in (("fullpay_equiv_weeks", "fullpay_equiv_weeks", ROLES),
                               ("paid_weeks_total", "paid_weeks_total", ROLES),
                               ("generic_plan_weeks", "generic_plan_weeks_max", ("birth",)),
                               ("protected_weeks_max", "protected_weeks_max", ROLES)):
        for suffix, x in (("", g), ("_disc", d)):
            for role in roles:
                row[f"{role}_{name}{suffix}"] = x[f"{field}_{role}"]
    floor = rec.get("statutory_floor") or {}
    row["statutory_floor_birth_weeks"] = floor.get("weeks_birth", "")
    row["statutory_floor_nonbirth_weeks"] = floor.get("weeks_nonbirth", "")
    row["term_weeks"] = g.get("term_weeks_used", "")
    row["term_source"] = TERM_SOURCE[g.get("term_source", "")]
    row["n_components"] = len(rec["components"])
    count = Counter(tiers[(rec["slug"], c["component_id"])] for c in rec["components"])
    for t in TIERS:
        row[f"n_{t}"] = count.get(t, 0)
    row["n_version_uncertain"] = flag_count(rec, "version_uncertain")
    row["n_pay_inferred"] = flag_count(rec, "ambiguous: pay level not stated; full pay inferred")
    for k in ("conditional_refusal", "scope_limits", "use_limits"):
        row[k] = g.get(k, "")
    return row


def build(out):
    meta = {r["institution_id"]: r for r in read_csv(ROOT / "reference" / "institutions.csv")}
    tiers = {(r["institution_id"], r["component_id"]): r["tier"] for r in read_csv(ROOT / "reference" / "component_tiers.csv")}
    terms = derive.term_weeks_2018()
    rows = []
    for inst_id in sorted(meta):
        with open(ROOT / "records" / f"{inst_id}.json", encoding="utf-8") as f:
            rec = json.load(f)
        rows.append(row_for(meta[inst_id], rec, tiers, terms))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    build(ap.parse_args().out)
