"""Derive summary figures from structured parental-leave policy records.

For each institution and parent role ("birth" = birth parent, "nonbirth" = non-birth parent after a birth; R5), the
figures are computed from the components of the institution's JSON record:

  leave_weeks_2018def    employer-funded leave (mechanisms employer_paid_leave, employer_childbirth_benefit,
                         employer_topup), guaranteed only unless --include-discretionary (R12).
                         Excludes own accruals (R1) and generic sick/disability plans (R2).
  relief_weeks_2018def   longest modified-duties (teaching relief) period, in weeks, same entitlement filter. Relief
                         linked `in_addition_to` a counted paid leave includes that leave (R3d).
  weeks_2018def          max(leave, relief)  (R3: record the longer partial-relief period). Among in_lieu_of
                         alternatives, the one with the most full-pay-equivalent weeks, ties to full pay (R15b).
  weeks_2018def_max      the same with duration_max (the upper value of a stated range) substituted (R13b)
  fullpay_equiv_weeks    employer-funded weeks x pay_fraction_pct/100 (R15b); components without a pay level
                         count at 100 with a note. pay_fraction_pct is read from the record or parsed from
                         pay_fraction (pay_fraction.py)
  relief_2018def         category of whichever of the two is longer: leave -> "All duties" (R9), except that a leave
                         whose counted components all keep research as a continuing duty takes its category from
                         its relief fields (R4c); relief -> "Just teaching" if research continues
                         (R4 collapse), else "Other".
  paid_weeks_total       all paid sources incl. government/state programs and paid generic plans,
                         excluding own accruals.
  protected_weeks_max    longest continuous period on job-protected leave because of the birth (rule U3(a)): counted
                         paid leaves (less paid relief that keeps research, R4c) and counted unpaid leaves (not
                         `general_purpose`, U1), each at its leave length for the role, placed in time with the
                         government benefits by the sequence links (R15). Leaves not joined by a placing link are
                         not added; the longest `in_lieu_of`-free track counts. Same entitlement filter.
  protected_basis        the leaves of that period with their placed weeks, and the links that place them
  unpaid_weeks_after_paid  protected_weeks_max minus paid_weeks_total, floored at 0 (rule U3(b)).

All-sources cap (R20): where a component states `cap_weeks_all_sources`, the smallest such cap bounds the employer
leave weeks (and so weeks_2018def and its _max), the full-pay-equivalent (scaled in proportion) and the paid total.
It is a cap on paid weeks, so it does not bound protected_weeks_max. Only a cap stated by a component counted for
the role and variant applies.
Leave limits (R20; record field `leave_limits`): the listed components together cover at most the stated weeks of
leave time, in the paid figures and in protected_weeks_max (clip_to_limits).
Link timing: a statute linked concurrent_with/within the institution's leaves starts with the earliest of them (S1;
place); components linked `also_available` (or `in_addition_to`) join one period for protected weeks and run one
after the other (R3d; GROUPING; place() already runs unlinked components in turn).

Overlaps (R15): the paid components are placed in time from their `sequence` relations (`concurrent_with` and
`within` start together, plus any `start_offset_weeks`; `consecutive_after` starts at the other's end) and the time
covered is counted once; for `in_lieu_of`, the alternative with the smaller full-pay-equivalent is dropped (R15b).
Components with no placing relation follow the others (assumed consecutive). Components paid
only from the employee's own balance (`payer: own_balance`), or from insurance the employee buys (`employee_paid`, R1d), are never counted (R1, R1b). Caregiver conditions are ignored, i.e. treated as gender-neutral (R6).

Unit conversion (R8, R11, R11b): week/workweek 1, day/workday 1/5, calendar_day 1/7, hour 1/40, month 52/12, year 52; terms use the
institution record's `calendar.term_weeks` if set, else the v1 coded weeks-per-term, else semester 16 /
quarter 11 / term 16 (the order is set by --term-precedence).
Every institution row carries a `notes` column listing assumptions and anything not convertible, a `scope_limits`
column listing leave and relief components whose population is limited (`faculty_scope`; counted or not, rule V3b),
a `conditional_refusal` column listing components granted unless the institution finds a stated ground (V2b),
and a `use_limits` column listing components with a stated limit on how many times they may be used (U9).

Usage (paths relative to the version folder, data/2018/v2.0/):
    python code/derive.py --records records --out derived.csv [--include-discretionary]
                          [--term-precedence {stated_calendar,stated_2018,calendar}]

Inputs read from the version folder (data/2018/v2.0/): records/<institution_id>.json, ../v1.0/parental_leave_policies.tsv (the v1
data set), reference/calendar_2017_18.csv and reference/programs.csv.

The rules cited by id (R3d, U5, V6, ...) are defined in guidance/rules.md.

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""

import argparse
import csv
import glob
import json
import re
from pathlib import Path

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from pay_fraction import pct as parse_pct  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
V1_TSV = ROOT.parent / "v1.0" / "parental_leave_policies.tsv"  # the v1.0 data set, in the sample's v1.0 folder
# Term length (R8): the 2017-18 calendar table (longest regular term, rounded up) and the orders in which the
# sources of a term's length are tried.
CALENDAR_CSV = ROOT / "reference" / "calendar_2017_18.csv"
TERM_PRECEDENCE = {
    "stated_2018": ("stated", "coding_2018", "kind_default"),               # alternative, for sensitivity analysis
    "stated_calendar": ("stated", "calendar", "coding_2018", "kind_default"),  # default, used for the data set
    "calendar": ("calendar", "stated", "coding_2018", "kind_default"),      # alternative, for sensitivity analysis
}
MISSING_FLOOR = []  # slugs derived without a statutory_floor (warned by main)
term_precedence = "stated_calendar"  # the default; set by --term-precedence

COUNTED_LEAVE = {"employer_paid_leave", "employer_childbirth_benefit", "employer_topup"}
EXCLUDE_CODES = {"excludes_main_faculty", "excludes_faculty"}
TOTAL_PAID = COUNTED_LEAVE | {"government_benefit", "generic_sick_or_disability_plan"}
GUARANTEED = {"guaranteed", "guaranteed_on_request"}
# payers whose pay is not the institution's: own balances (R1, R1b) and insurance the employee buys (R1d)
NOT_EMPLOYER_FUNDED = {"own_balance", "employee_paid"}
DEFAULT_TERM = {"semester": 16, "quarter": 11, "term": 16}
# U5: a leave for the birth parent's own illness or disability, marked by the flag OWN_ILLNESS_FLAG, counts in
# protected_weeks_max only up to OWN_ILLNESS_HORIZON weeks after the birth; one with no stated end counts to the
# horizon. The record keeps the stated length.
OWN_ILLNESS_FLAG = "own_illness_leave"
OWN_ILLNESS_HORIZON = 52.0
# U5: a leave to care for a seriously ill family member (flag FAMILY_ILLNESS_FLAG) counts for the
# non-birth parent in protected_weeks_max only, to the same horizon, and in no paid figure.
FAMILY_ILLNESS_FLAG = "family_illness_leave"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def calendar_weeks():
    """slug -> calendar-inferred term weeks (2017-18), or {} if the table is absent."""
    if not CALENDAR_CSV.exists():
        return {}
    with open(CALENDAR_CSV, encoding="utf-8") as f:
        return {r["slug"]: float(r["term_weeks_calendar"]) for r in csv.DictReader(f) if r["term_weeks_calendar"]}


_CALENDAR = None


def term_choice(rec, terms):
    """(term weeks used or None, source, candidates) under term_precedence."""
    global _CALENDAR
    if _CALENDAR is None:
        _CALENDAR = calendar_weeks()
    s, cal = rec["slug"], rec.get("calendar") or {}
    kind = cal.get("kind")
    # the 2017-18 calendar table applies only to records with a reference date in 2017-2019; a record with no
    # reference_date does not use it
    in_2017_18 = str(rec.get("reference_date") or "")[:4] in ("2017", "2018", "2019")
    cand = {"stated": cal.get("term_weeks"), "calendar": _CALENDAR.get(s) if in_2017_18 else None, "coding_2018": terms.get(s),
            "kind_default": DEFAULT_TERM.get(kind) if kind else None}
    for src in TERM_PRECEDENCE[term_precedence]:
        if isinstance(cand[src], (int, float)):
            return cand[src], src, cand
    return None, "", cand


def term_weeks_2018():
    """weeks per term by institution slug, from the v1 data set (rows coded in 'term' units)."""
    out = {}
    with open(V1_TSV, encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            for g in ("woman", "man"):
                if r[f"paid_leave_len_{g}_units"].strip() == "term":
                    try:
                        out.setdefault(slug(r["university_name"]),
                                       float(r[f"paid_leave_weeks_{g}"]) / float(r[f"paid_leave_len_{g}"]))
                    except (ValueError, ZeroDivisionError):
                        pass
    return out


def to_weeks(dur, inst_slug, terms, notes):
    if not dur or dur.get("value") is None:
        return None
    v, u = float(dur["value"]), (dur.get("units") or "").lower()
    if u in ("week", "workweek"):
        return v
    if u == "calendar_day":  # R11b
        return v / 7
    if u in ("day", "workday"):
        return v / 5
    if u == "hour":
        return v / 40
    if u == "month":
        return v * 52 / 12
    if u == "year":
        return v * 52
    if u in DEFAULT_TERM:
        if isinstance(terms.get(("calendar", inst_slug)), (int, float)):  # institution record's own calendar
            return v * terms[("calendar", inst_slug)]
        if inst_slug in terms:
            return v * terms[inst_slug]
        notes.add(f"default {DEFAULT_TERM[u]} wk/{u}")
        return v * DEFAULT_TERM[u]
    notes.add(f"unconvertible unit '{u}'")
    return None


CAP_RX = re.compile(r"(\d+(?:\.\d+)?)\s*(weeks?|workweeks?|months?|days?|workdays?|hours?)", re.I)


def cap_weeks(v, s, terms, notes):
    """All-sources cap in weeks: a number (weeks), a duration dict, or text with a leading number and unit
    ("3 months (sick leave plus ...)"). Anything else is ignored, with a note."""
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict):
        return to_weeks(v, s, terms, notes)
    if isinstance(v, str):
        m = CAP_RX.search(v)
        if m:
            u = m.group(2).lower().rstrip("s")
            return to_weeks({"value": float(m.group(1)), "units": u}, s, terms, notes)
    notes.add("cap_weeks_all_sources not parseable; ignored")
    return None


def applies_to_main_faculty(c):
    flags = c.get("flags", [])
    # match the flag code (text before any ":"), not words in a free-text flag such as "ambiguous: ... excludes ..."
    if any(f.split(":")[0].strip() in EXCLUDE_CODES for f in flags):
        return False
    if any(f.startswith("not_yet_effective") for f in flags):  # rule V5
        return False
    if any(f.startswith("summary_only") for f in flags):  # source precedence: a component known only from a summary does not count
        return False
    fg = c.get("faculty_group")
    return fg is None or str(fg).startswith("main_campus")


def general_purpose(c):
    """U1: a general-purpose leave, paid or unpaid, is counted in no figure."""
    return any(f.startswith("general_purpose") for f in c.get("flags", []))


def over_service(c):
    """U8: a component that requires more than two years of service is outside the standard member the figures
    describe, and counts in no figure (flag `service_over_two_years`)."""
    return "service_over_two_years" in (c.get("flags") or [])


def for_role(c, role):
    """A sequence entry with `roles` applies only to those roles; for others it is dropped."""
    seq = c.get("sequence") or []
    if not any("roles" in s for s in seq):
        return c
    return {**c, "sequence": [s for s in seq if "roles" not in s or role in s["roles"]]}


def role_ok(c, role):
    ep = c.get("eligible_parent") or ["any_parent"]
    want = "birth_parent" if role == "birth" else "non_birth_parent"
    return want in ep or "any_parent" in ep


def overlaps(c):
    """Declared overlap relations: sequence entries plus component ids listed in runs_concurrently_with."""
    rels = [(r.get("relation"), r.get("component_id")) for r in (c.get("sequence") or [])]
    rels += [("concurrent_with", x) for x in (c.get("runs_concurrently_with") or []) if "_c" in str(x)]
    return rels


# The program table, reference/programs.tsv (kind, mechanism, waiting period), used to check records (M1, R21).
PROGRAMS_CSV = ROOT / "reference" / "programs.csv"
WAITING_MECHANISMS = ("government_benefit", "generic_sick_or_disability_plan")


def load_programs():
    if not PROGRAMS_CSV.exists():
        return []
    with open(PROGRAMS_CSV, encoding="utf-8") as f:
        return [dict(r, rx=re.compile(r["match"], re.I)) for r in csv.DictReader(f)]


PROGRAMS = load_programs()


def programs_named(c):
    """The program-table rows a benefit or plan names in its statute_source or label (never the description). They
    are used to check records (M1, R21); the derivation does not use them: the placement offsets are those coded in
    the record, which are checked against the table."""
    if c.get("mechanism") not in WAITING_MECHANISMS:
        return []
    text = f"{c.get('statute_source') or ''} {c.get('institution_label') or ''}"
    return [r for r in PROGRAMS if r["rx"].search(text)]


STATUTE_NAME = re.compile(r"\bFMLA\b|Family and Medical Leave Act|\bCFRA\b|California Family Rights|\bPDL\b|Pregnancy Disability Leave|"
                          r"New Parent Leave Act|\bNPL\b|\bWFLA\b|Family Care Act|Parental Leave Act|Code\b", re.I)


NOT_STATUTE_NAME = re.compile(r"\bnon-?\s*FMLA|other than (the )?FMLA", re.I)


def is_statute(c):
    """A statutory leave (rule S1): an unpaid leave with a statute_source, or named for a statute in its label.
    The free-text description is not read (a childbearing leave described as running with "(PDL)" is not a
    statute)."""
    name = c.get("institution_label") or ""
    if NOT_STATUTE_NAME.search(name):  # "Non-FMLA Medical Leave", "Disability Leave (other than FMLA/CFRA/PDL)"
        name = ""
    return c.get("mechanism") == "unpaid_leave" and bool(c.get("statute_source") or STATUTE_NAME.search(name))


FLOOR_STATUTE = {"US": re.compile(r"\bFMLA\b|Family and Medical Leave Act|Family Medical Leave Act", re.I),
                 "CA": re.compile(r"Employment Standards|Labour Standards|Saskatchewan Employment Act|\bESA\b", re.I)}


def floor_statute(c, country):
    """A component that is the statute behind the record's statutory floor (FMLA in the US; the provincial
    employment-standards act in Canada): the floor is then not added a second time to its group."""
    rx = FLOOR_STATUTE["US" if country == "US" else "CA"]
    text = f"{c.get('institution_label') or ''} {c.get('description') or ''} {c.get('statute_source') or ''}"
    return c.get("mechanism") == "unpaid_leave" and bool(rx.search(text))


def leave_limits(rec, role, include_disc=False):
    """leave_limits (R20): [(weeks, component ids)] that apply to this role. A limit the institution may waive at
    its discretion (`waivable_at_discretion`: true) binds the guaranteed figures only."""
    return [(float(x["weeks"]), set(x["components"])) for x in rec.get("leave_limits") or []
            if role in (x.get("roles") or ["birth", "nonbirth"])
            and not (include_disc and x.get("waivable_at_discretion"))]


def paid_caps(rec, role):
    """`paid_caps` [{weeks, components, roles?}]: a cap on the paid weeks of named benefits
    together. Applied like leave_limits, but in the paid figures only (never in protected weeks)."""
    return [(float(x["weeks"]), set(x["components"])) for x in rec.get("paid_caps") or []
            if role in (x.get("roles") or ["birth", "nonbirth"])]


def clip_within(span, comps, start, weeks):
    """`within` ("ends no later"; R15): a component placed `within` another stops at that one's end. span:
    {id: (start, end)} for the components measured; comps are all components placed (measured ones and their
    anchors), and containers are read from start/weeks. Nested containment uses each container's clipped end, not
    its raw end."""
    end = {a: start[a] + weeks[a] for a in start}
    pairs = []
    for c in comps:
        a = c["component_id"]
        # R15: where consecutive_after places the component, a `within` entry states only that the two overlap
        if a not in start or any(s.get("relation") == "consecutive_after" and s.get("component_id") in start
                                 for s in c.get("sequence") or []):
            continue
        pairs += [(a, s.get("component_id")) for s in c.get("sequence") or []
                  if s.get("relation") == "within" and s.get("component_id") in start and s.get("component_id") != a]
    for _ in range(len(pairs) + 1):  # propagate clipped ends through nesting; stops early when nothing changes
        changed = False
        for a, b in pairs:
            new = max(start[a], min(end[a], end[b]))
            if new < end[a] - 1e-9:
                end[a], changed = new, True
        if not changed:
            break
    return {a: (lo, min(hi, end.get(a, hi))) for a, (lo, hi) in span.items()}


def clip_to_limits(span, limits):
    """Leave limits (R20): the listed components together cover at most `weeks`. Their spans are cut at the
    point where their covered time reaches the limit. span: {id: (start, end)}; returns a new dict."""
    span = dict(span)
    for cap, ids in limits or []:
        listed = sorted((span[i][0], span[i][1], i) for i in ids if i in span)
        covered, end, cut = 0.0, None, None
        for a, b, _ in listed:
            a = a if end is None else max(a, end)
            if b <= a:
                continue
            if covered + (b - a) >= cap:
                cut = a + cap - covered
                break
            covered, end = covered + b - a, b
        if cut is not None:
            for a, b, i in listed:
                span[i] = (min(a, cut), min(b, cut))
    return span


def pay_pct(c):
    v = c.get("pay_fraction_pct")
    if v is None:
        v = parse_pct(c.get("pay_fraction"))
    return v


def drop_alternatives(comps, weeks, weeks_cmp=None):
    """R15b: among in_lieu_of alternatives, keep the option with the larger full-pay-equivalent (weeks x pct),
    compared at the stated maximum (weeks_cmp, i.e. duration_max where a range is given); ties go to the
    higher pay level, then to the longer period, then to the earlier component.
    Options are compared as whole tracks: of the sets of components that contain no in_lieu_of pair and cannot
    be extended, the best is kept, so a track of several components (a top-up, then a further top-up) is weighed
    against its alternative as a whole (resolving one pair at a time could drop part of the better track).
    Relief periods are chosen on the timeline instead (figure() in derive()). Paid components keep this ranking: placing
    the tracks would reward an alternative whose removal leaves a benefit linked to it unplaced, which R15 then runs
    after the rest."""
    ids = [c["component_id"] for c in comps]
    by_id = {c["component_id"]: c for c in comps}
    wc = weeks_cmp or weeks
    conflict = {cid: set() for cid in ids}
    for c in comps:
        for relation, other in overlaps(c):
            if relation == "in_lieu_of" and other in by_id and other != c["component_id"]:
                conflict[c["component_id"]].add(other)
                conflict[other].add(c["component_id"])
    linked = [cid for cid in ids if conflict[cid]]
    if not linked:
        return comps
    if len(linked) > 16:
        raise ValueError(f"{len(linked)} components linked in_lieu_of; too many to compare as tracks")

    def key(sel):
        w = [wc[x] or 0 for x in sel]
        fp = sum(wx * (pay_pct(by_id[x]) or 100) / 100 for wx, x in zip(w, sel))
        return (fp, fp / sum(w) if sum(w) else 0.0, sum(w))

    best, best_key = None, None
    for mask in range(1, 2 ** len(linked)):
        sel = [x for i, x in enumerate(linked) if mask >> i & 1]
        if any(conflict[x] & set(sel) for x in sel):
            continue  # contains a pair of alternatives
        if any(not conflict[x] & set(sel) for x in linked if x not in sel):
            continue  # could be extended
        k = key(sel)
        # first-found wins ties: masks with the earlier component set come first among equal keys
        if best_key is None or k > best_key or (k == best_key and sorted(map(linked.index, sel)) < sorted(map(linked.index, best))):
            best, best_key = sel, k
    dropped = set(linked) - set(best)
    return [c for c in comps if c["component_id"] not in dropped]


def placing_relations(comps, weeks):
    """(a, b, gap, kind) for every relation that places component a relative to b: a starts `gap` weeks after b
    starts. kind is "same" (concurrent_with/within, gap = start_offset_weeks) or "after" (consecutive_after,
    gap = b's weeks). A stated offset wins over the reciprocal entry of the same pair, which would say gap 0."""
    ids = {c["component_id"] for c in comps}
    rel = []
    for c in comps:
        a = c["component_id"]
        n = len(c.get("sequence") or [])
        for s in c.get("sequence") or []:
            b, r = s.get("component_id"), s.get("relation")
            if b not in ids or b == a:
                continue
            if r in ("concurrent_with", "within"):
                rel.append((a, b, float(s.get("start_offset_weeks") or 0), "same"))
            elif r == "consecutive_after":
                rel.append((a, b, weeks[b], "after"))
        rel += [(a, x, 0.0, "same") for _, x in overlaps(c)[n:] if x in ids]
    offset = {(a, b) for a, b, g, k in rel if k == "same" and g}
    rel = [(a, b, g, k) for a, b, g, k in rel if not (k == "same" and not g and (b, a) in offset)]
    # A component that runs alongside two leaves which are also available to each other (R3d: they add) starts with
    # the first of them; it does not pull the second onto the same start (S1: the statute runs from the earliest
    # leave).
    aa = {frozenset((c["component_id"], s.get("component_id"))) for c in comps for s in c.get("sequence") or []
          if s.get("relation") == "also_available"}
    kept, out, extra = {}, [], []
    for a, b, g, k in rel:
        if k == "same" and not g:
            first = next((x for x in kept.get(a, []) if frozenset((b, x)) in aa), None)
            if first is not None:
                # R3d: leaves also available to each other add; the second starts when the first ends
                extra.append((b, first, weeks[first], "after"))
                continue
            kept.setdefault(a, []).append(b)
        out.append((a, b, g, k))
    placed_after = {a for a, b, g, k in out if k == "after"}
    return out + [e for e in extra if e[0] not in placed_after]


def place(comps, weeks):
    """Start week of each component under R15: `concurrent_with`/`within` start with the other component
    (plus `start_offset_weeks`), `consecutive_after` starts when the other ends; components with no placing relation
    follow everything placed so far. `consecutive_after` is applied first, then `concurrent_with`/`within` with a stated
    offset, then the rest, which then only say the components overlap."""
    ids = [c["component_id"] for c in comps]
    rel = placing_relations(comps, weeks)
    # R15: a component consecutive_after several others starts when the last of them ends and
    # never sets their start; any of them that nothing else places run one after another, ending where it starts.
    preds = {}
    for a, b, g, k in rel:
        if k == "after":
            preds.setdefault(a, set()).add(b)
    multi = {a: bs for a, bs in preds.items() if len(bs) > 1}
    rel = [r for r in rel if not (r[3] == "after" and r[0] in multi)]
    start, cursor = {}, 0.0
    order = [i for i in ids if i not in multi] + [i for i in ids if i in multi]
    for root in order:
        if root in start:
            continue
        if root in multi and all(b in start for b in multi[root]):
            start[root] = max(start[b] + weeks[b] for b in multi[root])
        else:
            start[root] = cursor
        while True:  # priority: consecutive_after, then a stated offset, then plain overlap
            step = next(((a, b, gap) for tier in (lambda k, g: k == "after", lambda k, g: k == "same" and g,
                                                  lambda k, g: k == "same" and not g)
                         for a, b, gap, k in rel if tier(k, gap) and (a in start) != (b in start)), None)
            if step is None:
                late = next((a for a, bs in multi.items() if a not in start and all(b in start for b in bs)), None)
                if late is not None:
                    start[late] = max(start[b] + weeks[b] for b in multi[late])
                    continue
                early = next((a for a, bs in multi.items() if a in start and any(b not in start for b in bs)), None)
                if early is None:
                    break
                end = start[early]  # its unplaced predecessors run one after another, ending where it starts
                for b in reversed([b for b in ids if b in multi[early] and b not in start]):
                    start[b] = end - weeks[b]
                    end = start[b]
                continue
            a, b, gap = step
            if b in start:
                start[a] = start[b] + gap
            else:
                start[b] = start[a] - gap
        cursor = max(start[x] + weeks[x] for x in start)
    # S1: a statute linked concurrent_with/within the institution's leaves
    # starts when the earliest of them starts, unless an offset or S1a places it. The leaves' own links set
    # their order; where they have none, they start together with the statute.
    statute = {c["component_id"] for c in comps if is_statute(c)}
    alongside = {(a, b) for a, b, g, k in rel if k == "same" and not g and (a in statute) != (b in statute)}
    for st in statute:
        if all((a, b) in alongside for a, b, g, k in rel if st in (a, b)):
            linked = [b if a == st else a for a, b in alongside if st in (a, b)]
            if linked:
                start[st] = min(start[x] for x in linked)
    return start


TIMED = COUNTED_LEAVE | {"unpaid_leave", "government_benefit", "modified_duties", "generic_sick_or_disability_plan",
                         "own_accrual"}
def anchors(measured, pool, weeks):
    """R18: the components that place the measured ones in time but are not measured
    themselves (for the paid figures, chiefly the unpaid leave a top-up and a benefit are both linked to). Followed
    link by link in both directions from the measured components; a component linked `in_lieu_of` one already
    included (an alternative, including those drop_alternatives removed) is left out, and so are components with no
    length. Without them, links to an unmeasured component would be dropped and the components would fall back to
    running one after another (R15). Links are read from sequence entries only (runs_concurrently_with names
    statutes, S1)."""
    ids = {c["component_id"] for c in measured}
    by_id = {c["component_id"]: c for c in pool if c.get("mechanism") in TIMED and weeks.get(c["component_id"]) is not None}
    inc = dict((c["component_id"], c) for c in measured)

    def alternative(x):
        return any(r == "in_lieu_of" and o in inc for r, o in overlaps(x)) or \
            any(r == "in_lieu_of" and o == x["component_id"] for y in inc.values() for r, o in overlaps(y))

    grew = True
    while grew:
        grew = False
        for x in list(by_id.values()):
            xid = x["component_id"]
            if xid in inc or alternative(x):
                continue
            # S1, R18: a statute running alongside the leaves (linked `concurrent_with` with no offset, a parallel
            # protection) does not set their order, so it does not anchor them; R15's default order stands. A link
            # `within` a statute, `consecutive_after`, or with an offset (S1a) places like any link (e.g. top-ups
            # within provincial employment-standards leaves; paid FMLA within FMLA).
            stat = is_statute(x)

            def alongside(s):
                return stat and s.get("relation") == "concurrent_with" and not s.get("start_offset_weeks")
            out = any(s.get("relation") in PLACING and s.get("component_id") in inc and not alongside(s)
                      for s in x.get("sequence") or [])
            into = any(s.get("relation") in PLACING and s.get("component_id") == xid and not alongside(s)
                       for y in inc.values() for s in y.get("sequence") or [])
            if out or into:
                inc[xid], grew = x, True
    return [c for i, c in inc.items() if i not in ids]


def combine(comps, weeks, weight=None, weeks_cmp=None, limits=None, pool=None, pool_weeks=None):
    """R15: place the components in time and measure the time covered by at least one; overlapping time counts
    once, at the highest weight then in effect. Alternatives are resolved first (R15b)."""
    return measure(drop_alternatives(comps, weeks, weeks_cmp), weeks, weight, limits, pool, pool_weeks)


def measure(comps, weeks, weight=None, limits=None, pool=None, pool_weeks=None):
    """The time covered by at least one of comps, placed in time (R15), at the highest weight then in effect.
    pool: the other components of the role, from which the anchors that place comps are taken (R18); pool_weeks
    their lengths (an unpaid leave at its leave length). Only comps are measured."""
    if not comps:
        return 0.0
    w = weight or (lambda c: 1.0)
    pw = pool_weeks or {}
    length = {k: (pw.get(k) if pw.get(k) is not None else weeks.get(k)) for k in set(pw) | set(weeks)}
    extra = anchors(comps, pool or [], length) if pool else []
    wk = {**{c["component_id"]: length[c["component_id"]] for c in extra}, **weeks}
    placed = list(comps) + extra
    start = place(placed, wk)
    span = clip_to_limits(clip_within({c["component_id"]: (start[c["component_id"]], start[c["component_id"]] + wk[c["component_id"]])
                                       for c in comps}, placed, start, wk), limits)
    spans = [(*span[c["component_id"]], w(c)) for c in comps]
    cuts = sorted({x for a, b, _ in spans for x in (a, b)})
    total = 0.0
    for lo, hi in zip(cuts, cuts[1:]):
        active = [wt for a, b, wt in spans if a <= lo and b >= hi]
        if active:
            total += (hi - lo) * max(active)
    return total


PLACING = ("concurrent_with", "within", "consecutive_after")
# R3d: components a parent may both take with no stated order are one period, one after
# the other (the longest-leave convention): they join a group for protected weeks; place() already runs them in turn.
GROUPING = PLACING + ("also_available", "in_addition_to")


def tracks(comps):
    """Every maximal set of components with no `in_lieu_of` pair among them (component ids)."""
    ids = [c["component_id"] for c in comps]
    conflict = {i: set() for i in ids}
    for c in comps:
        for r, o in overlaps(c):
            if r == "in_lieu_of" and o in conflict and o != c["component_id"]:
                conflict[c["component_id"]].add(o)
                conflict[o].add(c["component_id"])
    linked = [i for i in ids if conflict[i]]
    free = [i for i in ids if not conflict[i]]
    if not linked:
        return [ids]
    if len(linked) > 20:
        raise ValueError(f"{len(linked)} components linked in_lieu_of; too many to compare as tracks")
    out = []
    for mask in range(1, 2 ** len(linked)):
        sel = [x for k, x in enumerate(linked) if mask >> k & 1]
        if any(conflict[x] & set(sel) for x in sel) or any(not conflict[x] & set(sel) for x in linked if x not in sel):
            continue
        out.append(free + sel)
    return out


def groups(comps):
    """Sets of components connected by placing relations (either direction)."""
    ids = {c["component_id"] for c in comps}
    adj = {i: set() for i in ids}
    for c in comps:
        for r, o in overlaps(c):
            if r in GROUPING and o in ids and o != c["component_id"]:
                adj[c["component_id"]].add(o)
                adj[o].add(c["component_id"])
    seen, out = set(), []
    for c in comps:
        if c["component_id"] in seen:
            continue
        stack, g = [c["component_id"]], set()
        while stack:
            x = stack.pop()
            if x not in g:
                g.add(x)
                stack.extend(adj[x] - g)
        seen |= g
        out.append([d for d in comps if d["component_id"] in g])
    return out


def cover(spans):
    """Weeks covered by at least one of the (start, end) spans."""
    total, end = 0.0, None
    for a, b in sorted(spans):
        if end is None or a > end:
            total, end = total + b - a, b
        elif b > end:
            total, end = total + b - end, b
    return total


def r1(x):
    """One decimal, half up, after removing floating-point noise (37 x 0.95 = 35.15 -> 35.2)."""
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(str(round(x, 9))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def own_illness(c):
    return OWN_ILLNESS_FLAG in (c.get("flags") or [])


def family_illness(c):
    return FAMILY_ILLNESS_FLAG in (c.get("flags") or [])


def horizon_capped(c, role):
    """U5 (birth: own illness; non-birth: family illness): counted in protected weeks to the horizon. An open-ended
    leave for a disability or medical need that is not an
    own-illness leave (pregnancy or childbirth disability; a medical leave for self or family) also counts to the
    horizon, for each parent it serves (flag `open_ended_medical_leave`)."""
    if "open_ended_medical_leave" in (c.get("flags") or []):
        return True
    return own_illness(c) if role == "birth" else family_illness(c)


def job_protected(c):
    """U3: weeks of the leave with a guaranteed job (`job_protected_weeks`), or None (all of it)."""
    v = c.get("job_protected_weeks")
    return float(v) if isinstance(v, (int, float)) else None


def clip_own_illness(span, by_id, role="birth"):
    """U5: own-illness (birth) and family-illness (non-birth) leaves end at OWN_ILLNESS_HORIZON weeks after the
    birth (week 0); a span starting later goes. U3: a leave counts only for its job-protected weeks."""
    out = {}
    for i, (a, b) in span.items():
        jp = job_protected(by_id[i]) if i in by_id else None
        if jp is not None:
            if jp <= 0:
                continue
            b = min(b, a + jp)
        if i in by_id and horizon_capped(by_id[i], role):
            if a >= OWN_ILLNESS_HORIZON:
                continue
            b = min(b, OWN_ILLNESS_HORIZON)
        out[i] = (a, b)
    return out


def protected_period(comps, weeks, limits=None, floor=None, country="", role="birth", open_ids=frozenset(), spans_out=None):
    """U3(a): the longest continuous period covered by at least one leave. Leaves and
    government benefits are placed in time within each group joined by placing relations (R15); benefits only place
    the leaves. Groups are not added to each other; every `in_lieu_of`-free track is tried and the longest kept.
    Returns (weeks, basis), the basis naming the leaves with their placed weeks and the links of that group (in weeks
    from the group's earliest leave). If spans_out is a dict, it receives the counted span of each leave of that group
    in weeks after the birth: {short id: (start, end)}.
    Statutory floor (U7; record field `statutory_floor`): the national or provincial statutory leave runs alongside
    each group from its earliest leave (S1), unless the group already holds that statute; with no counted leave at
    all, the floor alone is the period."""
    by_id = {c["component_id"]: c for c in comps}
    short = lambda i: i.split("_")[-1]  # noqa: E731

    best, basis = (floor or 0.0), (f"statutory floor[0-{round(floor, 1):g}]" if floor else "")
    best_uses_floor = bool(floor)  # on a tie, prefer the leaves that reach the figure without the floor
    for track in tracks(comps):
        for g in groups([by_id[i] for i in track]):
            members = [c for c in g if c.get("mechanism") != "government_benefit"]
            if not members:
                continue
            # A leave with no stated end (counted to the horizon under U5, or an open-ended medical leave) places
            # nothing after it: it is placed with length 0, then covers from its start to the horizon (a 52-week
            # placeholder would push a following parental leave past week 52)
            pw = {i: (0.0 if i in open_ids else w) for i, w in weeks.items()}
            start = place(g, pw)
            span = clip_to_limits(clip_within({c["component_id"]: (start[c["component_id"]], start[c["component_id"]] + pw[c["component_id"]])
                                               for c in members}, members, start, pw), limits)
            for i in open_ids:
                if i in span:
                    span[i] = (span[i][0], max(span[i][0], OWN_ILLNESS_HORIZON))
            span = clip_own_illness(span, by_id, role)  # U5; U3 (job-protected weeks)
            if not span:
                continue
            if floor and not any(floor_statute(c, country) for c in members):
                low0 = min(a for a, _ in span.values())
                span["statutory floor"] = (low0, low0 + floor)
            total = cover(span.values())
            uses_floor = "statutory floor" in span and cover(v for k, v in span.items() if k != "statutory floor") < total
            if total > best or (total == best and best_uses_floor and not uses_floor):
                g_ids = {c["component_id"] for c in g}
                low = min(a for a, _ in span.values())
                leaves = " ".join(f"{short(i)}[{round(a - low, 1):g}-{round(b - low, 1):g}]" for i, (a, b) in sorted(span.items(), key=lambda x: x[1]))
                links = ", ".join(f"{short(c['component_id'])} {r} {short(o)}" + (f" +{s['start_offset_weeks']:g}" if s.get("start_offset_weeks") else "")
                                  for c in g for s in (c.get("sequence") or []) for r, o in [(s.get("relation"), s.get("component_id"))]
                                  if r in GROUPING and o in g_ids)
                best, basis, best_uses_floor = total, leaves + (f"; links: {links}" if links else ""), uses_floor
                if spans_out is not None:
                    spans_out.clear()
                    spans_out.update({short(i): (round(a, 1), round(b, 1)) for i, (a, b) in span.items() if i != "statutory floor"})
    return best, basis


def relief_category(c):
    rel = c.get("relief") or {}
    if rel.get("teaching") in ("relieved", "partially_relieved") and rel.get("research") == "continues":
        return "Just teaching"
    return "Other"


def leave_category(kept, wk):
    """R4c: a paid leave is "All duties" (R9) unless every counted leave component
    keeps research as a continuing duty (stated, or unnamed under R4b); then the category comes from the relief
    fields of the longest one, as for modified duties (R4)."""
    kept = [c for c in kept if wk[c["component_id"]]]
    if kept and all((c.get("relief") or {}).get("research") == "continues" for c in kept):
        return relief_category(max(kept, key=lambda c: wk[c["component_id"]]))
    return "All duties"


def component_weeks(c, role, s, terms, notes, use_max=False):
    """Weeks for this component and role: duration_by_role > paid_duration (paid share) > duration.
    With use_max, duration_max (the upper value of a stated range, R13b) replaces duration where present."""
    dur = (c.get("duration_by_role") or {}).get(role) or c.get("paid_duration") or c.get("duration")
    if use_max and c.get("duration_max") and dur is c.get("duration"):
        dur = c["duration_max"]
    return to_weeks(dur, s, terms, notes)


def use_limit_text(entry):
    """'1 per career', '1 per 3 years', '2 children per career' (U9)."""
    what = "children" if entry.get("counts") == "children" else ""
    per = f"{entry.get('window_years'):g} years" if entry.get("per") == "window" else entry.get("per")
    return f"{entry.get('times')} {what + ' ' if what else ''}per {per}"


def use_limits_column(components):
    """The `use_limits` flag column (U9): every component with a stated limit."""
    out = []
    for c in components:
        lims = [e for e in c.get("use_limit") or [] if isinstance(e, dict)]
        if lims:
            # no counted label: whether a component counts depends on the figure
            out.append(f"{c['component_id']} ({c.get('mechanism')}): " + ", ".join(use_limit_text(e) for e in lims))
    return "; ".join(out)


def derive(rec, terms, include_disc):
    s = rec["slug"]
    out = {"institution": rec["institution"], "slug": s, "country": rec.get("country", "")}
    notes = set()
    if not rec.get("statutory_floor"):
        # U7: every record carries its statutory floor; a missing one is a data error
        notes.add("NO statutory_floor: protected weeks lack the U7 floor (the record has no statutory_floor)")
        MISSING_FLOOR.append(s)
    tw, tsrc, tcand = term_choice(rec, terms)
    if tw:
        terms = dict(terms)
        terms[("calendar", s)] = tw
        notes.add(f"term = {tw:g} wk ({tsrc})")
    for role in ("birth", "nonbirth"):
        limits = leave_limits(rec, role, include_disc)  # R20: stated limits on leave time
        time_limits = limits  # protected weeks: leave-time limits only
        limits = limits + paid_caps(rec, role)  # the paid figures also respect paid_caps
        weeks = {c["component_id"]: component_weeks(c, role, s, terms, notes) for c in rec["components"]}
        weeks_max = {c["component_id"]: component_weeks(c, role, s, terms, notes, use_max=True) for c in rec["components"]}
        # unpaid leaves at their leave length for this role: duration_by_role, else duration (never the paid share)
        unpaid_w = {c["component_id"]: to_weeks((c.get("duration_by_role") or {}).get(role) or c.get("duration"), s, terms, notes)
                    for c in rec["components"]}
        ok_ent = lambda c: include_disc or c.get("entitlement") in GUARANTEED
        # R18: lengths of the components that may anchor the paid ones in time; a leave at its leave length
        anchor_w = {c["component_id"]: (unpaid_w if c.get("mechanism") == "unpaid_leave" else weeks)[c["component_id"]]
                    for c in rec["components"]}
        base = [for_role(c, role) for c in rec["components"]
                if applies_to_main_faculty(c) and role_ok(c, role) and not general_purpose(c) and not over_service(c)]
        # all-sources cap: only from components counted for this role and variant (R20)
        caps = [cap_weeks(c.get("cap_weeks_all_sources"), s, terms, notes) for c in base
                if c.get("cap_weeks_all_sources") and ok_ent(c)]
        caps = [x for x in caps if x is not None]
        cap = min(caps) if caps else None
        # U5: family-illness leave counts in no paid figure for the non-birth parent
        pay_base = [c for c in base if not (role == "nonbirth" and family_illness(c))]
        leave = [c for c in pay_base if c.get("mechanism") in COUNTED_LEAVE and ok_ent(c)
                 and c.get("payer") not in NOT_EMPLOYER_FUNDED and weeks[c["component_id"]] is not None]  # R1, R1b
        relief = [c for c in pay_base if c.get("mechanism") == "modified_duties" and ok_ent(c)]
        for c in relief:
            if weeks[c["component_id"]] is None:
                notes.add(f"{c['component_id']} relief not convertible to weeks")

        def figure(wk):
            leave_ids = {c["component_id"] for c in leave}

            default = {c["component_id"] for c in drop_alternatives(relief, wk, weeks_max)}

            def full_pay(c):
                return (pay_pct(c) or 100) >= 100

            def linked(x, y):
                return any(r in GROUPING and o == y["component_id"] for r, o in overlaps(x)) or \
                    any(r in GROUPING and o == x["component_id"] for r, o in overlaps(y))

            def chain(c, kept, by_id):
                """R3f: full-pay relief periods linked to each other form one combined period. Relief
                with a pay cut is never chained (R3)."""
                if not full_pay(c):
                    return [c]
                ids, todo = {c["component_id"]}, [c]
                while todo:
                    x = todo.pop()
                    for y in kept:
                        if y["component_id"] not in ids and full_pay(y) and linked(x, y):
                            ids.add(y["component_id"])
                            todo.append(y)
                return [by_id[i] for i in ids]

            def combined(c, kept, by_id, sink):
                """The relief period for the v1 definition, read from the timeline: the chain of full-pay relief
                periods (R3f) and the counted paid leaves linked to it are placed in time (R15) and the time covered
                is measured. A leave `within` the relief adds nothing (R3b); a leave the relief follows
                (`consecutive_after`), or one also available with no order stated, adds (R3d)."""
                ch = chain(c, kept, by_id)
                if len(ch) > 1:
                    sink.add(f"{c['component_id']} relief combined with {len(ch) - 1} further full-pay relief period(s) (R3f)")
                with_leave = [x for x in leave if wk[x["component_id"]] is not None and any(linked(x, y) for y in ch)]
                # the linked leaves are placed before the relief, so relief that is also available with several leaves
                # follows all of them (R3d, R18: 6 + 6 + 16 = 28, not 22)
                parts = with_leave + ch
                start = place(parts, wk)
                # R20: a stated leave limit that lists relief periods caps them too (e.g. modified duties plus
                # childbearing and bonding leave that 'will not exceed the equivalent of two quarters').
                span = clip_to_limits({x["component_id"]: (start[x["component_id"]], start[x["component_id"]] + wk[x["component_id"]])
                                       for x in parts}, limits)
                total = cover([span[x["component_id"]] for x in parts])
                relief_only = cover([span[x["component_id"]] for x in ch])
                if any(span[x["component_id"]][1] < start[x["component_id"]] + wk[x["component_id"]] - 1e-9 for x in parts):
                    sink.add(f"{c['component_id']} relief period cut by a stated leave limit (R20)")
                if total > relief_only + 1e-9:
                    sink.add(f"{c['component_id']} relief combined with the paid leave it follows (R3d)")
                return total

            # R15b on the timeline: each in_lieu_of-free set of relief periods is measured with the
            # leaves it is linked to, and the set giving the longest period kept; ties to the set chosen by pay (R15b)
            relief_w, best_key = [], None
            for track in tracks(relief):
                kept = [c for c in relief if c["component_id"] in track and wk[c["component_id"]] is not None]
                by_id = {c["component_id"]: c for c in kept}
                sink = set()  # notes only from the set kept
                rws = [(combined(c, kept, by_id, sink), c) for c in kept]
                k = (round(max((x for x, _ in rws), default=0.0), 6), set(track) >= default)
                if best_key is None or k > best_key:
                    relief_w, best_key, best_notes = rws, k, sink
            notes.update(best_notes if best_key is not None else ())
            lw = combine(leave, wk, weeks_cmp=weeks_max, limits=limits, pool=base, pool_weeks=anchor_w) if leave else 0.0
            if cap is not None and lw > cap:
                notes.add(f"employer leave capped at {cap} wk (all-sources cap)")
                lw = cap
            rw, rc = max(relief_w, key=lambda t: t[0]) if relief_w else (0.0, None)
            if rw > lw:
                return lw, rw, rw, relief_category(rc)
            return lw, rw, lw, (leave_category(drop_alternatives(leave, wk, weeks_max), wk) if lw > 0 else "")

        lw, rw, w18, cat = figure(weeks)
        _, _, w18_max, _ = figure(weeks_max)
        for c in leave:
            if pay_pct(c) is None:
                notes.add(f"{c['component_id']} pay level not stated; counted at 100% in fullpay_equiv")
        fp = combine(leave, weeks, weight=lambda c: (pay_pct(c) or 100) / 100, weeks_cmp=weeks_max, limits=limits,
                     pool=base, pool_weeks=anchor_w) if leave else 0.0
        uncapped = combine(leave, weeks, weeks_cmp=weeks_max, limits=limits, pool=base, pool_weeks=anchor_w) if leave else 0.0
        if cap is not None and uncapped > cap:
            fp *= cap / uncapped  # same cap, applied in proportion to the pay-weighted weeks
        # Total paid: employer-funded leave + government/state programs (guaranteed), no own accruals.
        # Generic sick/disability plans are reported separately: their stated maxima cover any illness
        # (e.g. "up to six months") and are not childbirth durations.
        paid = [c for c in pay_base if c.get("mechanism") in (COUNTED_LEAVE | {"government_benefit"})
                and c.get("payer") not in NOT_EMPLOYER_FUNDED and ok_ent(c) and weeks[c["component_id"]] is not None]
        for c in base:
            if c.get("mechanism") in TOTAL_PAID and weeks[c["component_id"]] is None:
                notes.add(f"{c['component_id']} ({c.get('mechanism')}) duration unknown, not in total")
        total = combine(paid, weeks, limits=limits, pool=base, pool_weeks=anchor_w) if paid else 0.0
        if cap is not None and total > cap:
            notes.add(f"total capped at {cap} wk (all-sources cap)")
            total = cap
        # R12: like every derived figure, generic_plan_weeks_max takes guaranteed plans only in the guaranteed
        # variant; discretionary plans count with --include-discretionary.
        gen = [c for c in pay_base if c.get("mechanism") == "generic_sick_or_disability_plan"
               and c.get("payer") not in NOT_EMPLOYER_FUNDED and ok_ent(c) and weeks[c["component_id"]] is not None]
        # V6: a plan's stages coded as components `consecutive_after` one another are one short-term entitlement;
        # generic_plan_weeks_max measures the chain (e.g. 16 weeks at full pay, then 10 at 60% -> 26)
        gid = {c["component_id"]: c for c in gen}
        nxt = {}
        for c in gen:
            for sq in c.get("sequence") or []:
                if sq.get("relation") == "consecutive_after" and sq.get("component_id") in gid:
                    nxt.setdefault(sq["component_id"], []).append(c["component_id"])

        def chain_weeks(i, seen=()):
            return weeks[i] + max((chain_weeks(j, seen + (i,)) for j in nxt.get(i, []) if j not in seen), default=0.0)
        generic = [chain_weeks(c["component_id"]) for c in gen]
        unpaid = [c for c in base  # general-purpose leaves are already out of base (U1)
                  if c.get("mechanism") == "unpaid_leave" and ok_ent(c) and unpaid_w[c["component_id"]] is not None]
        # U5: a leave with no stated end that horizon_capped() selects counts to the horizon (protected weeks only).
        # The own-illness rule is about the birth parent's own illness; for the non-birth parent horizon_capped()
        # applies the family-illness test instead.
        open_ill = [c for c in base if c.get("mechanism") == "unpaid_leave" and ok_ent(c) and horizon_capped(c, role)
                    and unpaid_w[c["component_id"]] is None]
        # U5: a paid family-illness leave still gives the non-birth parent job-protected leave
        fam_paid = [c for c in base if role == "nonbirth" and family_illness(c) and c.get("mechanism") in COUNTED_LEAVE
                    and ok_ent(c) and weeks[c["component_id"]] is not None]
        out[f"leave_weeks_2018def_{role}"] = r1(lw)
        out[f"relief_weeks_2018def_{role}"] = r1(rw)
        out[f"weeks_2018def_{role}"] = r1(w18)
        out[f"weeks_2018def_max_{role}"] = r1(w18_max)
        out[f"relief_2018def_{role}"] = cat
        out[f"fullpay_equiv_weeks_{role}"] = r1(fp)
        out[f"paid_weeks_total_{role}"] = r1(total)
        out[f"generic_plan_weeks_max_{role}"] = r1(max(generic)) if generic else 0.0
        # U3(a): paid leaves and benefits from the paid total, less paid relief that keeps research (R4c),
        # with the counted unpaid leaves. Leaves at their leave length for the role, benefits at their weeks.
        held = [c for c in paid if not (c.get("mechanism") in COUNTED_LEAVE
                                        and (c.get("relief") or {}).get("research") == "continues")] + unpaid + open_ill + fam_paid
        # U3: a dedicated leave paid only from the employee's own balances, or by insurance the employee buys
        # (R1, R1b, R1d), is still a leave: it counts in protected weeks, though not in the paid figures
        held += [c for c in base if c.get("mechanism") in ("employer_paid_leave", "employer_childbirth_benefit")
                 and c.get("payer") in NOT_EMPLOYER_FUNDED and ok_ent(c) and weeks[c["component_id"]] is not None
                 and (c.get("relief") or {}).get("research") != "continues"]
        held_w = {c["component_id"]: (weeks if c.get("mechanism") == "government_benefit" else unpaid_w)[c["component_id"]]
                  or weeks[c["component_id"]] or (OWN_ILLNESS_HORIZON if horizon_capped(c, role) else None) for c in held}
        # not capped by cap_weeks_all_sources, which caps paid weeks; bounded by leave_limits (R20)
        floor = (rec.get("statutory_floor") or {}).get(f"weeks_{role}")
        spans = {}
        protected, basis = protected_period(held, held_w, time_limits, floor, rec.get("country", ""), role,
                                            frozenset(c["component_id"] for c in open_ill), spans)
        out[f"protected_weeks_max_{role}"] = r1(protected)
        out[f"protected_basis_{role}"] = basis
        out[f"protected_spans_{role}"] = spans  # the same leaves, in weeks after the birth (for the policy viewer)
        out[f"unpaid_weeks_after_paid_{role}"] = r1(max(0.0, protected - total))
    # V3b: make partial coverage visible downstream. Every leave or relief component whose population is limited
    # (faculty_scope set), whether counted as main campus or not; and every counted component granted subject to a
    # conditional refusal (V2b).
    scoped = [c for c in rec["components"]
              if c.get("faculty_scope") and c.get("mechanism") in (COUNTED_LEAVE | {"modified_duties"})]
    out["scope_limits"] = "; ".join(
        f"{c['component_id']} ({c['mechanism']}, {'counted' if applies_to_main_faculty(c) else 'not counted'}): "
        f"{c['faculty_scope']}" for c in scoped)
    out["use_limits"] = use_limits_column(rec["components"])  # U9
    for k in ("stated", "calendar", "coding_2018"):
        out[f"term_weeks_{k}"] = "" if tcand[k] is None else f"{tcand[k]:g}"
    out["term_weeks_used"], out["term_source"] = ("" if tw is None else f"{tw:g}"), tsrc
    out["conditional_refusal"] = "; ".join(
        c["component_id"] for c in rec["components"]
        if any(f.startswith("conditional_refusal") for f in c.get("flags", [])))
    flags = [f for c in rec["components"] for f in c.get("flags", []) if f.startswith("ambiguous")]
    out["n_components"] = len(rec["components"])
    out["n_ambiguous_flags"] = len(flags)
    out["missing"] = rec.get("missing", False)
    if out["missing"] and out["missing"] != "partial":
        # The governing policy was not obtained: the figures are not determinable, not zero.
        for k in list(out):
            if k.endswith(("_birth", "_nonbirth")):
                out[k] = ""
        notes.add(f"figures not determinable: {out['missing']}")
    out["notes"] = "; ".join(sorted(notes))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", default=str(ROOT / "records"))
    ap.add_argument("--out", default=str(ROOT / "derived.csv"))
    ap.add_argument("--include-discretionary", action="store_true")
    ap.add_argument("--term-precedence", choices=sorted(TERM_PRECEDENCE), default="stated_calendar",
                    help="order of the sources for a term's length: stated_calendar (stated, then the 2017-18 calendar, then v1; "
                         "the default, used for the data set), stated_2018 (stated, then v1) or calendar (the "
                         "calendar first); the last two are alternatives for sensitivity analysis")
    a = ap.parse_args()
    global term_precedence
    term_precedence = a.term_precedence
    terms = term_weeks_2018()
    rows = [derive(json.load(open(p, encoding="utf-8")), terms, a.include_discretionary)
            for p in sorted(glob.glob(str(Path(a.records) / "*.json")))]
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {a.out}")
    if MISSING_FLOOR:
        print(f"WARNING: {len(set(MISSING_FLOOR))} records have no statutory_floor (U7); protected weeks may be too low. "
              f"Check the records' statutory_floor field.", file=sys.stderr)


if __name__ == "__main__":
    main()
