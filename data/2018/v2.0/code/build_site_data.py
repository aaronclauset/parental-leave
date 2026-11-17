"""Export each institution's components on a timeline, per parent, for the website's policy viewer.

Usage (from the version folder, data/2018/v2.0/):
    python code/build_site_data.py [--out timelines.json]

For each institution and parent (birth, non-birth), the components that cover main-campus tenure-stream faculty and
that parent are listed. Those that are periods of leave, pay or relief (derive.TIMED) are placed in time by their
sequence links, as derive.py places them (R15): `concurrent_with` and `within` start together (plus any stated
offset), `consecutive_after` starts when the other ends, and unlinked components follow what is already placed.
The others (tenure-clock stops, part-time options, donated leave, other provisions) are listed with no start. A component with no convertible length (an open-ended leave, a duration
in courses) is placed with length 0 and marked `open`, with its stated quantity (`amount`, for example "2 courses",
empty when none is stated) and, where the derivation counts it in job-protected weeks (U3, U5), the span it counts
(`counted`, [start, end] in weeks after the birth, from the derivation's protected_spans in either variant;
otherwise null). The viewer draws one timeline from these placements; the
figures in the data set place the components each figure counts separately, so a figure's period can differ from
the span of the whole drawing. Values are in weeks after the birth.

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import derive  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "timelines.json"
FIGURES = ("weeks_2018def", "relief_2018def", "paid_weeks_total", "protected_weeks_max")


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def r1(x):
    return None if x is None else round(float(x), 1)


PLACED_AFTER = ("consecutive_after", "within", "concurrent_with")


def dependency_order(comps):
    """The components ordered so that each comes after those it is placed by (consecutive_after, within,
    concurrent_with), so that place() starts every chain at its first component; record order breaks ties."""
    ids = [c["component_id"] for c in comps]
    by_id = {c["component_id"]: c for c in comps}
    deps = {i: {s.get("component_id") for s in by_id[i].get("sequence") or []
                if s.get("relation") in PLACED_AFTER and s.get("component_id") in by_id and s.get("component_id") != i}
            for i in ids}
    out, done = [], set()

    def visit(i, path=()):
        if i in done or i in path:
            return
        for d in sorted(deps[i], key=ids.index):
            visit(d, path + (i,))
        done.add(i)
        out.append(by_id[i])

    for i in ids:
        visit(i)
    return out


def amount(c):
    """The stated quantity of a component with no length in weeks, as words ("2 courses", "up to 6 months"), or ""."""
    d = c.get("duration") or {}
    if not isinstance(d, dict) or d.get("value") in (None, "") or not d.get("units"):
        return ""
    v, u = d["value"], str(d["units"])
    unit = u if v == 1 else u + "s"
    return f"{'up to ' if d.get('qualifier') == 'up_to' else ''}{v:g} {unit}" if isinstance(v, (int, float)) else f"{v} {unit}"


def counted_spans(rec, role, terms):
    """{short component id: [start, end]}: the spans the derivation counts in job-protected weeks for this parent, in
    weeks after the birth (derive's protected_spans), in the guaranteed or the discretionary variant (the longer
    where both)."""
    out = {}
    for disc in (False, True):
        for cid, (a, b) in (derive.derive(rec, terms, disc).get(f"protected_spans_{role}") or {}).items():
            if cid not in out or b - a > out[cid][1] - out[cid][0]:
                out[cid] = [a, b]
    return out


def timeline(rec, role, terms, tiers):
    s = rec["slug"]
    notes = set()
    comps = [derive.for_role(c, role) for c in rec["components"]
             if derive.applies_to_main_faculty(c) and derive.role_ok(c, role)]
    weeks = {c["component_id"]: derive.component_weeks(c, role, s, terms, notes) for c in comps}
    spans = counted_spans(rec, role, terms)
    timed = [c for c in comps if c.get("mechanism") in derive.TIMED]
    lengths = {c["component_id"]: (weeks[c["component_id"]] if weeks[c["component_id"]] is not None else 0.0)
               for c in timed}
    start = derive.place(dependency_order(timed), lengths) if timed else {}
    if start and min(start.values()) < 0:  # a leave stated to begin before the birth: shift so the drawing starts at 0
        shift = -min(start.values())
        start = {k: v + shift for k, v in start.items()}
    out = []
    for c in comps:
        cid = c["component_id"]
        out.append({"id": cid.rsplit("_", 1)[-1], "label": c.get("institution_label") or "",
                    "mechanism": c.get("mechanism", ""),
                    "entitlement": c.get("entitlement", ""), "payer": c.get("payer", ""),
                    "pay_pct": derive.pay_pct(c), "tier": tiers.get((s, cid), ""),
                    "general_purpose": derive.general_purpose(c), "over_two_years": derive.over_service(c),
                    "start": r1(start.get(cid)), "weeks": r1(weeks[cid]), "open": weeks[cid] is None,
                    "amount": amount(c) if weeks[cid] is None else "",
                    "counted": spans.get(cid.rsplit("_", 1)[-1]) if weeks[cid] is None else None,
                    "links": [{"relation": q.get("relation"), "to": str(q.get("component_id", "")).rsplit("_", 1)[-1]}
                              for q in c.get("sequence") or []],
                    "doc_ids": c.get("doc_ids") or []})
    return sorted(out, key=lambda x: (x["start"] is None, x["start"] or 0.0, int(x["id"].lstrip("c") or 0)))


def build(out):
    meta = {r["institution_id"]: r for r in read_csv(ROOT / "reference" / "institutions.csv")}
    tiers = {(r["institution_id"], r["component_id"]): r["tier"] for r in read_csv(ROOT / "reference" / "component_tiers.csv")}
    terms = derive.term_weeks_2018()
    data = {}
    for inst_id in sorted(meta):
        with open(ROOT / "records" / f"{inst_id}.json", encoding="utf-8") as f:
            rec = json.load(f)
        g, d = derive.derive(rec, terms, False), derive.derive(rec, terms, True)
        entry = {"institution": meta[inst_id]["institution"], "values_available": not g["missing"]}
        for role in ("birth", "nonbirth"):
            entry[role] = {"components": timeline(rec, role, terms, tiers),
                           "guaranteed": {f: g[f"{f}_{role}"] for f in FIGURES},
                           "with_discretionary": {f: d[f"{f}_{role}"] for f in FIGURES}}
        data[inst_id] = entry
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    print(f"wrote {len(data)} institutions to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    build(ap.parse_args().out)
