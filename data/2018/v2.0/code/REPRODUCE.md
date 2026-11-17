# Reproducing the data files

Every derived file in this version folder (`data/2018/v2.0/`): the data set, the differences file and the website's timeline data, is computed from the structured records in `records/`, the tables in `reference/` and the v1.0 file in `../v1.0/`, by the code in this folder. No step is done by hand.

## Requirements
Python 3.9 or later. Only the standard library is used.

## Commands
Run from this version's folder, `data/2018/v2.0/`:

```
python code/build_csv.py          # parental_leave_2018_v2.0.csv
python code/build_differences.py  # v1_v2_differences.csv
python code/build_site_data.py    # timelines.json
python code/test_rebuild.py       # rebuilds all three and checks them byte for byte against the released copies
```

`python code/derive.py --records records --out derived.csv [--include-discretionary]` writes every derived figure, per institution, with the derivation's notes. It is a fuller table than the CSV.

## What each file does
| File | Role |
|---|---|
| `derive.py` | Computes each figure from a record, by the rules in `guidance/rules.md` (the rule ids are cited in the code) |
| `pay_fraction.py` | Reads a pay level ("full pay", "one-half", "95%") from a component's `pay_fraction` text |
| `build_csv.py` | Writes the data set CSV: institution metadata, both variants of every figure, and the counts and flags |
| `build_differences.py` | Compares v2.0 with v1 for each institution and attaches the cause of each disagreement |
| `build_site_data.py` | Places each institution's components on a timeline, per parent, for the website's policy viewer |
| `statutory_floor.py` | Gives each record's statutory floor (rule U7) from `reference/statutory_baseline.csv`; run alone, it lists any record whose floor differs |
| `test_rebuild.py` | Checks that the three files above are reproduced exactly, and that every record's statutory floor matches the table |

## Inputs
| File | Content |
|---|---|
| `records/<institution_id>.json` | One structured record per institution (format: `guidance/schema.md`) |
| `reference/institutions.csv` | Institution metadata: name, country, region, state or province, control, AAU membership (January 2018), prestige rank |
| `reference/component_tiers.csv` | The tier of every component (primary, secondary, tertiary, contextual) |
| `reference/calendar_2017_18.csv` | Term lengths from the institutions' 2017–18 academic calendars, with the calendar each was read from (rule R8, step 2: first day of classes to last day of exams, less recesses of three or more weekdays, for the longest regular term, rounded up to whole weeks) |
| `reference/programs.csv` | Government programs: kind, mechanism and waiting period (rules M1, R21) |
| `reference/v1_v2_causes.csv` | The cause and a short explanation of each disagreement between v1 and v2.0 |
| `../v1.0/parental_leave_policies.tsv` | The v1.0 data set, unchanged; read for v1's values and term lengths |
