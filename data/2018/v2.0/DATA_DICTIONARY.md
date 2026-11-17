# Data dictionary: faculty parental-leave policies, 2018, version 2.0

## The file
- **File:** `parental_leave_2018_v2.0.csv`: UTF-8, comma-separated, one header row.
- **Rows:** 205, one per institution in the v1.0 sample. v1.0 also had a row for the Polytechnic Institute of NYU (now NYU Tandon), which repeated New York University's policy; it is not kept.
- **Reference date:** every value describes the policies in force in the **2017–18 academic year** (each record's `reference_date` gives the date its documents were read), for **tenured and tenure-track faculty on the main campus** who become parents through a **birth**, with up to two years of service.
- **Values unavailable:** for 5 institutions the governing faculty policies were not publicly accessible. Their value columns are empty, and `values_available` is `no`.
- **Units:** all durations are in weeks, rounded to one decimal place. A week is 5 working days or 7 calendar days. An academic term is converted to weeks as described under `term_weeks`.

## Parents and variants
- **Birth parent:** the parent who gives birth. **Non-birth parent:** the birth parent's partner. Adoption and foster provisions are recorded in the structured encodings but counted in neither role.
- **Guaranteed** values count benefits a faculty member is entitled to, including those granted on request. Columns ending `_disc` also count benefits the institution may grant or refuse, or that are negotiated.

## Columns

### Identity and context
| Column | Meaning |
|---|---|
| `institution` | Name as in the 2018 data set |
| `institution_id` | Stable identifier, used in the structured encodings and the other release files |
| `country` | `US` or `Canada` |
| `region` | U.S. census region (`Northeast`, `Midwest`, `South`, `West`) or `Canada` |
| `state_province` | Two-letter state or province code; `CA-federal` for the Naval Postgraduate School, a federal institution in California whose leave follows federal rules |
| `control` | `public` or `private` |
| `aau_member_2018` | `1` if a member of the Association of American Universities in January 2018, else `0` |
| `prestige_rank` | Field-general prestige rank of Wapman et al. (2022), 1 = most prestigious; U.S. only, empty where not ranked |
| `values_available` | `yes`, or `no` if the governing policies were not publicly accessible |

### Primary values (the measure of the 2018 data set)
For each parent, the longer of (a) weeks of paid leave funded by the employer and (b) weeks of relief from duties at full pay. Relief that follows a counted leave adds to it. Pay drawn only from the faculty member's own sick or vacation balances counts as zero, and so does a general sick-leave or disability plan with no childbirth-specific provision. An employer's top-up of a government benefit counts. Among alternatives, the one worth the most weeks at full pay counts.

| Column | Meaning |
|---|---|
| `birth_weeks`, `nonbirth_weeks` | Primary value, guaranteed |
| `birth_relief`, `nonbirth_relief` | Kind of relief over that period: `all duties` (a leave), `teaching only` (teaching relieved, research continuing), `other` (relief of another kind), or empty when the value is 0 |
| `birth_weeks_max`, `nonbirth_weeks_max` | The same, reading any stated range at its upper value (the main columns use the lower value) |
| `birth_weeks_disc`, `nonbirth_weeks_disc`, `birth_relief_disc`, `nonbirth_relief_disc`, `birth_weeks_max_disc`, `nonbirth_weeks_max_disc` | The same three, also counting discretionary or negotiated benefits |

### Secondary values
| Column | Meaning |
|---|---|
| `birth_fullpay_equiv_weeks`, `nonbirth_fullpay_equiv_weeks` (and `_disc`) | Weeks of employer-funded pay, each weighted by the share of salary paid |
| `birth_paid_weeks_total`, `nonbirth_paid_weeks_total` (and `_disc`) | Weeks with any pay because of the birth, from any source (employer, government benefit, insurance), excluding the faculty member's own balances; overlapping periods count once |
| `birth_generic_plan_weeks` (and `_disc`) | Weeks a birth parent can be paid through a general sick-leave or disability plan, at its short-term entitlement |
| `birth_protected_weeks_max`, `nonbirth_protected_weeks_max` (and `_disc`) | Longest continuous period of job-protected leave because of the birth, including statutory leave. **A maximum:** some leaves require a medical condition. Leaves for the parent's own illness, or (for the non-birth parent) for care of the birth parent, count only up to 52 weeks after the birth |
| `statutory_floor_birth_weeks`, `statutory_floor_nonbirth_weeks` | Job-protected leave guaranteed by statute in the institution's jurisdiction on 1 January 2018 (U.S. FMLA, 12 weeks; Canadian provincial employment standards) |

### How the values were computed
| Column | Meaning |
|---|---|
| `term_weeks` | Weeks per academic term, used to convert values stated in terms to weeks |
| `term_source` | Where `term_weeks` comes from, in order of precedence: `policy` (stated in the policy), `calendar` (the institution's 2017–18 academic calendar: first day of classes to last day of exams, less recesses of three or more weekdays, longest regular term, rounded up), `v1` (the term length v1.0 used), `default` (16 for a semester or term, 11 for a quarter). Filled whenever a term length is known for the institution, and used only for values stated in terms; empty when none is known |

### Policy structure
| Column | Meaning |
|---|---|
| `n_components` | Number of components (distinct provisions) in the institution's structured encoding |
| `n_primary`, `n_secondary`, `n_tertiary`, `n_contextual` | Components by tier: primary (paid leave and relief that can set the primary value); secondary (unpaid job-protected leave, government benefits, short-term sick-leave or disability plans); tertiary (provisions no value measures, such as tenure-clock stops, part-time return, own balances, donated leave); contextual (other faculty groups, staff, adoption only, or general-purpose leaves) |

### Flags for sensitivity analyses
| Column | Meaning |
|---|---|
| `n_version_uncertain` | Components resting on a document whose version in force on the reference date could not be confirmed |
| `n_pay_inferred` | Relief components with no stated pay level, read as full pay |
| `conditional_refusal` | Benefits granted unless the institution makes a stated finding (for example "undue burden"), listed by component; counted as guaranteed |
| `scope_limits` | Leave or relief provisions limited to one college or unit, which are not counted for the main campus |
| `use_limits` | Stated limits on how often a benefit can be used (for example "1 per career"), listed by component |

## Related files
- **`records/`:** the structured encoding of each institution's policy, with the verbatim quotes behind every coded field.
- **`guidance/`:** the coding rules, schema, coding checklist, field meanings and reader instructions.
- **`v1_v2_differences.csv`:** for each institution, the v1.0 and v2.0 primary values for each parent, whether they agree (weeks within 1 and the same relief category, for the guaranteed values and with discretionary provisions), and the cause and a short explanation of each disagreement. Causes: `rule_difference`, `v1_missing_now_found`, `v1_error`, `not_determinable`, `different_reference_date`, `discretionary_provisions`.
- **`provenance/index.csv`:** one row per source document a record lists or cites: its original URL, web-archive capture (`wayback_url`, `wayback_timestamp`), retrieval date, type, size, SHA-256 and version; `note` says how the copy was obtained; `cited_by` lists the components that cite the document by `doc_ids`, and `quoted_by` those with a quote of six or more words found in its saved text (statutes only for the institution's own jurisdiction). The documents themselves are not released.
- **`reference/`:** the tables the CSV is built from (institution metadata, component tiers, the 2017–18 calendar term lengths, government programs, the causes).
- **`code/`:** the code that rebuilds every data file from the records; `code/REPRODUCE.md` says how.
- **Column names in the code:** the derivation (`code/derive.py`) names the primary value `weeks_2018def_<parent>`, its range maximum `weeks_2018def_max_<parent>`, the relief kind `relief_2018def_<parent>`, and the secondary values `fullpay_equiv_weeks_`, `paid_weeks_total_`, `generic_plan_weeks_max_` and `protected_weeks_max_<parent>`; `build_csv.py` renames them as above.

## Versions
- **v2.0 (2026):** this file, a recollection of the 2018 data set from the institutions' own documents in force in the 2017–18 academic year. It is the current version.
- **v1.0 (2018):** the data set as originally published, in `../v1.0/` (`data/2018/v1.0/` in the repository). Its values are not repeated in this file; how v1.0 and v2.0 differ is described in the release notes.

## Citation and license
- **v2.0:** A. Clauset, "Faculty parental-leave policies at U.S. and Canadian universities, 2018 v2.0" (2026), https://github.com/aaronclauset/parental-leave.
- **v1.0:** A. C. Morgan, S. F. Way, M. Galesic, D. B. Larremore and A. Clauset, "Paid parental leave at US and Canadian universities" (2018).
- **License:** both versions, and the structured encodings, guidance and reference tables, are released under the Creative Commons Attribution 4.0 International License (CC BY 4.0). The code is released under the BSD 3-Clause license. The verbatim quotes in the structured encodings are short excerpts of documents whose copyright remains with their owners; they are included so that every coded value can be checked against its source.
