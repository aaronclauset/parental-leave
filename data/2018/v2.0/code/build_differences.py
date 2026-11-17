"""Compare the data set (v2.0) with the original data set (v1), institution by institution.

Usage (from the version folder, data/2018/v2.0/):
    python code/build_differences.py [--out v1_v2_differences.csv]

Reads ../v1.0/parental_leave_policies.tsv (the v1.0 data set), parental_leave_2018_v2.0.csv and reference/v1_v2_causes.csv,
and writes one row per institution with the v1 and v2 primary values for each parent, whether they agree, and, where
they do not, the cause and a short explanation. Values agree when the weeks are within 1 and the relief category is
the same; v1's "Not specified" matches any category, and two values of 0 agree whatever their category. Where v1
has no value, the parent is not compared; where v1 has a value and v2 has none (not determinable), they differ. Agreement is
given for the guaranteed values and for the values with discretionary provisions.

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "v1_v2_differences.csv"
V1_TSV = ROOT.parent / "v1.0" / "parental_leave_policies.tsv"  # the v1.0 data set, in the sample's v1.0 folder
V1_RELIEF = {"All duties": "all duties", "Just teaching": "teaching only", "Other": "other"}
ROLES = (("birth", "woman"), ("nonbirth", "man"))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def agree(v1_weeks, v1_relief, v2_weeks, v2_relief):
    """1 or 0; "" when v1 has no value. A v1 value with no v2 value (not determinable) is a disagreement."""
    a, b = num(v1_weeks), num(v2_weeks)
    if a is None:
        return ""
    weeks_ok = b is not None and abs(a - b) <= 1
    relief_ok = v1_relief in ("Not specified", "") or V1_RELIEF.get(v1_relief, v1_relief) == v2_relief or (a == 0 and b == 0)
    return int(weeks_ok and relief_ok)


def build(out):
    with open(V1_TSV, encoding="utf-8") as f:
        v1 = {r["university_name"]: r for r in csv.DictReader(f, delimiter="\t")}
    with open(ROOT / "parental_leave_2018_v2.0.csv", encoding="utf-8") as f:
        v2 = list(csv.DictReader(f))
    with open(ROOT / "reference" / "v1_v2_causes.csv", encoding="utf-8") as f:
        causes = {(r["institution_id"], r["variant"]): r for r in csv.DictReader(f)}
    rows, problems = [], []
    for r in v2:
        old = v1.get(r["institution"])
        if old is None:
            problems.append(f"{r['institution_id']}: not in v1")
            continue
        row = {"institution_id": r["institution_id"], "institution": r["institution"]}
        for role, g in ROLES:
            row[f"v1_{role}_weeks"] = old[f"paid_leave_weeks_{g}"]
            row[f"v1_{role}_relief"] = V1_RELIEF.get(old[f"relief_{g}"], old[f"relief_{g}"])
            row[f"v2_{role}_weeks"] = r[f"{role}_weeks"]
            row[f"v2_{role}_relief"] = r[f"{role}_relief"]
            row[f"v2_{role}_weeks_disc"] = r[f"{role}_weeks_disc"]
            row[f"v2_{role}_relief_disc"] = r[f"{role}_relief_disc"]
        for variant, suffix in (("guaranteed", ""), ("discretionary", "_disc")):
            flags = [agree(old[f"paid_leave_weeks_{g}"], old[f"relief_{g}"], r[f"{role}_weeks{suffix}"],
                           r[f"{role}_relief{suffix}"]) for role, g in ROLES]
            both = "" if all(x == "" for x in flags) else int(all(x in (1, "") for x in flags))
            row[f"agree_{variant}"] = both
            cause = causes.get((r["institution_id"], variant), {})
            if both == 0 and not cause:
                problems.append(f"{r['institution_id']} ({variant}): differs, but no cause")
            if both == 1 and cause:
                problems.append(f"{r['institution_id']} ({variant}): agrees, but a cause is listed")
            row[f"cause_{variant}"] = cause.get("category", "") if both == 0 else ""
            row[f"explanation_{variant}"] = cause.get("explanation", "") if both == 0 else ""
        rows.append(row)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")
    for p in problems:
        print("PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    raise SystemExit(build(ap.parse_args().out))
