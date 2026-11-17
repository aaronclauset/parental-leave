# Reader instructions

These are the instructions a model reader receives to encode one institution's parental-leave documents into a structured record. They are version 1.25, the version under which the 2018 data set v2.0 was produced. They are read with the interpretive rules (`rules.md`), the schema (`schema.md`), the coding checklist (`coding_checklist.md`) and the field meanings (`field_meanings.md`), which share their version number.

Throughout, **v1.0** means the earlier data set: the faculty parental-leave data published with Morgan, Way, Galesic, Larremore and Clauset (2018), with its corrections through January 2019. This release (**v2.0**) re-collects the same institutions from the policies in force in the 2017–18 academic year.

The same guidance governs later collections (a 2026 collection is under way); the examples are from the 2018 data. Published with the data: the records, this guidance, `programs.csv`, `statutory_baseline.csv`, the 2017–18 calendar table (`calendar_2017_18.csv`), the code and the provenance index. Not published: the source documents and saved statute texts (identified by URL and web-archive capture in the provenance index), the passage index, the readers' reports, and the checker the readers ran (`check_extraction.py`), which tests a record against the saved source texts.

You extract parental-leave policy provisions for the institution you are given, from saved policy documents, into one JSON record per institution. Your complete instructions are these instructions, the **coding checklist**, the schema, the rules, the field meanings, the program table (`programs.csv`), the statutory baseline and the saved statute texts. Your task states the institution, its sources, the reference date and the reference period.

**Version.** These instructions, `coding_checklist.md`, `schema.md`, `rules.md` and `field_meanings.md` all carry version 1.25. If they don't, stop and report it.

## 1. Inputs

| Input | Content |
|---|---|
| Task | The institution; the `reference_date`; the `reference_period` (the academic year an undated document may come from); the guidance version every record is stamped with (in `codebook_version` and `schema_version`) |
| Sources | The institution's usable saved documents, each with its URL and capture date |
| Passage index | Where provided: likely-relevant spans, to help you find sections. It does not replace reading the files |
| **Coding checklist** | `coding_checklist.md`: what to extract (§1), how to code each field (§2), the record-level items (§3) and the decision log (§4). **Your working order** |
| Schema | `schema.md`: every field's format and codes; use them exactly |
| Rules | `rules.md`: open the rules the checklist points you to, whenever your case is not the checklist's default |
| Field meanings | `field_meanings.md`: what each published figure means |
| Program table | `programs.csv`: each government program's kind and mechanism (M1) and its waiting period (R21) |
| Statutory baseline | `statutory_baseline.csv`: the rows for the institution's country and its state or province. `verified: yes` rows were checked against the saved statute; `no` rows only prompt your search, never as evidence. (The published table holds only the `yes` rows.) |
| Statute texts | The saved statute texts, always readable (rule U2). A statute may also be saved among the institution's own sources |

**Open nothing else.** Never open v1.0's coding of the institution or any other reader's record. Do not use the web or your own knowledge of an institution. A document that names a policy that is not saved: flag `cross_reference_not_saved`.

**Governing document cited but not saved.** `summary_only` applies when the saved governing document covers the topic and does not contain the provision, or contradicts the summary. When the governing document that sets a provision is cited but not saved, a summary, HR or provost page that states the provision supplies it: code it as stated, flag it `cross_reference_not_saved: <title>`, and do not flag it `summary_only`. If no governing document for faculty leave is saved at all, the rule for records with no governing document applies (§3, step 1).

**Reference date.** Read each document as policy in force on the `reference_date`. A document that carries no version date is accepted as in force if its copy dates from the reference academic year (the task says which); record what the document shows about its date. A provision whose stated effective date falls after the reference date is flagged `not_yet_effective` (V5).

## 2. Population

Main-campus tenured and tenure-track faculty. Record every provision that covers them, and also provisions for other groups and provisions that exclude them: `faculty_group` says who is covered.

## 3. Procedure

1. **Read every usable source in full.** Eligibility, definitions, exclusions and cross-references are often far from the leave sections. Read a long source (more than about 2,000 lines) line by line in consecutive chunks from start to end, not by searching for terms. Report the line ranges you read for each file; they are a report of the reading, not part of the record. A file you show by a diff to be identical to another saved copy you have read in full counts as read in full. So does a file that differs from such a copy, if you diff the two, read every differing passage and list those passages in your report. A saved file that holds no policy (an index or navigation page) is noted as such in `notes`. **No governing document for faculty leave.** If none of the usable sources is a governing document for faculty leave that covers the institution's tenure-stream faculty (a collective agreement, a faculty handbook, or a leave, parental-leave, modified-duties or tenure-clock policy), set the record's `missing` to `no_policy_on_page`. Do this even when other sources state parental provisions for another group (staff) or only summarize them. Code every provision the sources describe, with its evidence and its faculty group, and say in `notes` what the sources contain and which governing document is missing. Still complete the accounting.
2. **Find every provision, class by class** (checklist §1). For each of the ten scope classes, record the components you found, or `absent` with the documents you searched and the terms you used, in `scope_accounting`. **Account for every statute named anywhere in the documents** (class C4): a component where U4 applies; otherwise listed under C4 `not_components` with the reason it is not one.
3. **Code each component field by field down checklist §2.** For each line, answer its question. Where your case is the default, code it. Where it is not, open the rules the line names, and code by them. Cite every rule you used in `rule_applied`. Where two governing documents in force on the reference date disagree, decide the reading by V3d and keep the other in a `conflicting_sources` flag.
4. **Log each judgment** (checklist §4): one `decision_log` entry for each field you decided by a rule or a reading, not for plain copies of the text. Keep entries short: the rule, the answer, the deciding quote.
5. **Give evidence:** verbatim quotes for the judgment fields (schema §2f). The `duration` quote carries the qualifier word ("up to", "at least", "normally"); the `entitlement` quote carries the grant wording.
6. **Restrictions go in coded fields.** A restriction you mention in a note must also appear in a coded field:
   - a child's age or time since the birth: `time_window`;
   - a school or unit: `faculty_scope`;
   - an appointment type: `faculty_group`;
   - service or appointment fraction: `service_requirement` (more than two years of service: also the flag `service_over_two_years`, U8);
   - role words: `eligible_parent` and its wording;
   - caregiver status: `caregiver_condition`;
   - a limit on leave time per event: `leave_limits`;
   - a limit on paid weeks across all sources: `cap_weeks_all_sources`;
   - a limit on the paid weeks of two or more named benefits together: `paid_caps`;
   - job protection for only part of a leave, or none: `job_protected_weeks`;
   - a waiting period: `start_offset_weeks` on the benefit's `sequence` entry, which anchors it to the leave or top-up (checklist §2, `sequence`; §5 example 1);
   - a limit on how many times a benefit may be used, or for how many children: `use_limit` (U9); a cap on total time off the tenure clock: the clock component's `duration_note`, with a flag (U9);
   - anything else: `ambiguous: restriction: <what>`.
7. **Record-level items** (checklist §3): leave limits, the paid-weeks caps, the calendar, the accounting. Do not fill `statutory_floor` or the institution metadata; they are filled from the tables.
8. **Do not change a rule.** A case the rules don't cover: code your best reading, flag `ambiguous: rule gap: <what>`, and report it.

## 4. Accounting (so that "absent" is a finding, not an omission)

- **Scope classes:** every class in checklist §1 has an entry in `scope_accounting`.
- **Passages:** every passage in the index is `used_in` (component ids) or `not_relevant` (a one-line reason).
- **Mechanism slots:** for each of the 12 mechanisms, the component ids, or `absent` with the documents and terms searched.
- **Baseline rows:** every statutory-baseline row for the jurisdiction is `components`, `absent` ("no saved document mentions it") or `not_applicable`. Never create a component from the baseline alone: the documents must mention the provision.

## 5. Output

Write one record, `<slug>.json`:

```json
{"institution": "...", "slug": "...", "country": "US | Canada",
 "model": "<exact model name>",
 "codebook_version": "1.25", "schema_version": "1.25",
 "reference_date": "<date used>",
 "calendar": {"term_weeks": 15, "note": "<quote>"} | {"kind": "semester", "note": "<quote>"},
 "documents": [{"doc_id": "...", "url": "...", "title": "..."}],
 "missing": false,
 "scope_accounting": {"C1": {"components": ["..."]} | {"absent": {"documents": ["<doc_id>"], "terms": ["..."]}}, "...": {}},
 "passage_dispositions": {"<passage_id>": {"used_in": ["..."]} | {"not_relevant": "reason"}},
 "mechanism_slots": {"employer_paid_leave": {"components": ["..."]} | {"absent": "..."}, "...": {}},
 "baseline_accounting": {"<baseline provision>": {"components": ["..."]} | {"absent": "..."} | {"not_applicable": "..."}},
 "leave_limits": [],
 "paid_caps": [],
 "components": [{"component_id": "<slug>_cN", "...schema fields...": "...",
                 "description": "...", "rule_applied": ["..."],
                 "evidence": {"<field>": ["verbatim quote"]}, "doc_ids": ["..."], "flags": [],
                 "decision_log": [{"field": "...", "rule": "<rule id, or schema, or source_precedence>", "answer": "...", "quote": "<verbatim>"}]}],
 "notes": ["..."]}
```

`calendar` only when a document states the term's length or kind: `term_weeks` for a stated length; `kind` alone, with `term_weeks` left empty, when only the kind of term is stated (R8). `doc_id` is the source file's stem (e.g. `2018_00_link`).

## 6. Before finishing

Run the checker (`check_extraction.py`) on your record.

- **Check each parent's chain.** For the birth parent and then the non-birth parent, write the order of their leaves and benefits in one line (e.g. "pregnancy leave 17 → recovery 6 → parental 35 → child's condition 5"; "EI maternity → EI parental"; "relief for the balance of the semester, containing the leave"). Confirm your `sequence` links give exactly that order, with no component linked two ways (e.g. after one component and within another that starts elsewhere). Put the two lines in `notes`.
- **Fix every ERROR** and run the checker again until none remain.
- **An error you believe is wrong:** say so in your report, with the test, your reason and the verbatim quote that supports your reading.
- **Warnings** are for your judgment: fix the record if the warning is right, otherwise leave it and mention it.

## 7. Report back (short)

For the institution:
- the components by scope class;
- what the documents did not let you determine;
- any rule you found hard to apply, or a case the rules don't cover;
- any checklist line that left you unsure;
- the errors you believe are wrong, and the warnings left standing.
