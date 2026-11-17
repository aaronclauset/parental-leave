# What each published field means

This file states what each value published in the data set means. It is version 1.25, the version under which the 2018 data set v2.0 was produced. It is read with the interpretive rules (`rules.md`), the schema (`schema.md`), the coding checklist (`coding_checklist.md`) and the reader instructions (`reader_instructions.md`), which share its version number. It states the meaning of the rules and the schema, and changes none of them; the derivation code (`derive.py`) computes what it says.

Throughout, **v1.0** means the earlier data set: the faculty parental-leave data published with Morgan, Way, Galesic, Larremore and Clauset (2018), with its corrections through January 2019. This release (**v2.0**) re-collects the same institutions from the policies in force in the 2017–18 academic year.

The same guidance governs later collections (a 2026 collection is under way); the examples are from the 2018 data. Published with the data: the records, this guidance, `programs.csv`, `statutory_baseline.csv`, the 2017–18 calendar table (`calendar_2017_18.csv`), the code and the provenance index. Not published: the source documents and saved statute texts (identified by URL and web-archive capture in the provenance index), the passage index, the readers' reports, and the checker the readers ran (`check_extraction.py`), which tests a record against the saved source texts.

For each figure the data set publishes, it gives four things:
- the question it answers;
- its definition;
- a worked example from the records;
- what it excludes.

## Common terms

- **Unit.** One institution's policy for main-campus tenured and tenure-track faculty, on the reference date.
  - **Reference date:** for records compared with v1.0, the date at which v1.0 recorded the institution's policy (its row date); 2018-01-01 for the records read at 2018-01-01 (the four institutions v1.0 recorded in January 2019, after the 2017–18 academic year) and for the statutory floor of the 2018 data; the collection date for 2026.
  - **Main campus:** a provision covering the units that hold the tenure-stream faculty in the arts and sciences, and in engineering where the institution has it (V3, V3b).
  - **Whom the figures describe:** a faculty member who has met the service requirements for eligibility (up to two years of service); a benefit that steps up after longer service is counted at the band for a member with two years of service, and a provision that requires more than two years of service counts in no figure (U8); the requirements are recorded per component. Where a benefit path depends on an election the member makes at hire, the figures take the more generous path (U8).
  - **Which policy:** where a university-wide and a unit-level policy differ, the university-wide one sets the figures (V3c). For a multi-campus system, "university-wide" means the campus: a campus-wide policy, including a provost's directive for the campus, is the institution's own policy. A system-wide policy also applies to the campus. Both are coded, and where they provide the same benefit, the more generous counts and neither adds to the other. Where two governing documents in force on the reference date disagree, V3d decides the reading.
- **Roles.** Every figure is given twice:
  - **birth parent**;
  - **non-birth parent**: the birth parent's partner, after a birth.

  Adoption, foster and surrogacy provisions are recorded but count in neither role (R5). Primary-caregiver and similar conditions are treated as gender-neutral (R6).
- **Variants.** Every figure is given twice:
  - **guaranteed:** provisions a faculty member is entitled to, including those granted on request where the approval sets only the arrangements;
  - **with discretionary:** adds provisions the institution may grant or refuse (R12, V2–V2d). A leave limit the institution may waive at its discretion (`waivable_at_discretion`) binds only the guaranteed variant (R20).
- **Weeks.** All lengths convert to weeks:
  - 5 working days, 7 calendar days or 40 hours = 1 week;
  - a month = 52/12 weeks; a year = 52 weeks;
  - a term = in order, the length a source states; the institution's academic calendar for the reference year (first day of classes to last day of exams, less recesses of three or more weekdays, for the longest regular term, rounded up to whole weeks); v1.0's term length for the institution; the default for the kind of term (semester 16, quarter 11, term 16) (R8, R11, R11b). The length used and its source are published as `term_weeks_used` and `term_source`.
- **Rounding.** Every figure is rounded to one decimal, half up.
- **Placement in time.** Components are placed by their links (R15). Where a component runs alongside two leaves that are also available to each other, the first starts with it and the second starts when the first ends; the two stay added.
- **Not counted anywhere.**
  - Provisions not yet in force on the reference date (V5).
  - Provisions that exclude main-campus faculty.
  - General-purpose leaves, paid or unpaid, that parents may also use but that exist for reasons other than health, family care or a birth or adoption; they are kept in the record and flagged `general_purpose` (U1). A list of purposes that is not exhaustive ('such as', 'including') counts as general.
  - Provisions found only in a summary or FAQ, not in the governing document; flagged `summary_only` (source precedence).
  - Provisions that require more than two years of service; flagged `service_over_two_years` (U8).

## The fields

### 1. Weeks of paid leave or relief, 2018 definition (`weeks_2018def`)
- **Question:** under v1.0's definition, how long is the employer-funded paid leave or teaching relief a new parent receives?
- **Definition:** the longer of two quantities (R3):
  - **(a)** the employer-funded paid leave, where "employer-funded" includes top-ups of government benefits (R7). The paid leave components are placed in time from their links (R15). Among alternatives, the one with the most full-pay-equivalent weeks counts; among relief alternatives, the one giving the longest relief period once placed with its linked leaves (R15b).
  - **(b)** the longest period of relief from duties at full pay, measured on the timeline:
    - relief for the rest of the semester in which a leave falls contains the leave, and the leave adds nothing (R3b);
    - relief that follows a paid leave, or may be taken as well with no order stated, adds the leave (R3d);
    - full-pay relief periods linked to each other combine (R3f);
    - relief for which the documents state no pay level, and no reduction, counts at full pay and is flagged `ambiguous: pay level not stated; full pay inferred (R3)`, so the figure can be computed without it.

  Relief or leave that comes with a pay cut smaller than the reduction in duties is coded with its pay level; it counts at its full length, and its pay level enters the full-pay-equivalent figure (R3). A range counts at its lower value (R13b). Pay the employer guarantees counts in full even if the employee's own balances are drawn first (R1c–R1e). Stated caps on paid weeks (`cap_weeks_all_sources`, `paid_caps`) and stated limits on leave time (`leave_limits`) limit it (R20).
- **Example:** Rutgers 2018, birth parent. A 6-week paid recuperative leave, plus up to 8 weeks of teaching release "for a total of up to fourteen weeks". That gives (a) = 6 and (b) = 14, so the figure is **14**.
- **Example (relief that contains the leave):** Boston University 2018. Workload reduction when "her Paid Absence for Childbirth ends before the semester is over", coded as one semester → **16** (R3b), not 6 + 16.
- **Excludes:**
  - pay only from the employee's own sick or vacation balances, or a colleague-funded bank (R1, R1b, R1d);
  - general sick or disability plans that are not a childbirth-specific benefit (R2, V1);
  - general-purpose leaves (U1);
  - government benefits not topped up;
  - unpaid leave;
  - a reduced appointment whose pay falls in proportion to its duties (R3; coded `part_time_option`);
  - paid time during which teaching and service are still required (R16).

### 2. Upper value of the same (`weeks_2018def_max`)
- **Question:** the same figure, when a stated range is read at its top.
- **Definition:** field 1 with each range at its upper value (R13b). v1.0 used the upper value.
- **Example:** Rochester 2018, birth parent: **6** (field 1) and **8** (this field).
- **Excludes:** as field 1.

### 3. Kind of relief, 2018 definition (`relief_2018def`)
- **Question:** what kind of relief does the field 1 period give: all duties, or teaching only?
- **Definition:** one of three categories:
  - **All duties:** field 1 comes from a leave that relieves every duty, or states no relief (R9);
  - **Just teaching:** teaching is relieved and research continues, whether stated or not named (R4, R4b). This includes a paid "leave" that keeps research (R4c);
  - **Other:** any other relief.
- **Example:** George Washington 2018. One semester "released from teaching and service" at full salary, with research not named → **14 weeks, Just teaching**.
- **Excludes:** nothing beyond field 1.

### 4. Full-pay-equivalent weeks (`fullpay_equiv_weeks`)
- **Question:** how many weeks of full salary does the employer-funded paid leave amount to?
- **Definition:** field 1(a), each week weighted by its pay level. Overlapping time counts once, at the highest pay level then in effect (R19, R15b). A component with no stated pay level counts at full pay, with a note. Stated caps on paid weeks (`cap_weeks_all_sources`, `paid_caps`) and leave limits apply (R20).
- **Example:** McGill 2018, birth parent. 20 weeks topped up to 100% of salary, then 11 weeks topped up to 60% → 31 weeks (field 1), **26.6** full-pay-equivalent.
- **Excludes:** as field 1. Relief periods are not included; this field measures paid leave only.

### 5. Total paid weeks (`paid_weeks_total`)
- **Question:** for how many weeks does a new parent receive any pay because of the birth, from any source?
- **Definition:** the time covered by at least one paid source:
  - employer leave and top-ups;
  - government or state benefits (EI, QPIP, state paid family leave; R7, R14, M1). A state disability insurance program is a generic plan (field 6), not counted here, unless the documents state a childbirth period with its length (M1; `programs.csv`).

  The sources are placed in time from their links (R15, R18); overlapping time counts once (R19); a government benefit starts after the statute's unpaid waiting period, whatever schedule the institution's text describes (R21; lengths in `programs.csv`). Stated caps limit it: a cap on all paid sources (`cap_weeks_all_sources`), a cap on the paid weeks of named benefits together (`paid_caps`), and limits on leave time (`leave_limits`) (R20).
- **Example:** Queen's 2018, birth parent. A 20-week maternity leave paid by the university and EI; EI maternity from week 2 (one-week wait), then EI parental benefits → **51**.
- **Example (waiting period):** Carleton 2018, birth parent. Two weeks at 95% salary (written for the old two-week EI wait), then a 15-week top-up during which the employee claims EI. EI maternity starts one week after the leave starts (the statute), and EI parental benefits follow it → **51**. The employer's schedule sets what it pays, not when EI starts.
- **Excludes:** pay only from the employee's own balances (R1) or from insurance the employee buys (R1d); general-purpose leaves (U1); leave to care for a seriously ill family member (flagged `family_illness_leave`; U5), which never counts in a paid figure; generic sick or disability plans, which are reported in field 6.

### 6. Generic plan weeks (`generic_plan_weeks_max`)
- **Question:** how long can a birth parent be paid through a general sick or disability plan that is not a childbirth benefit?
- **Definition:** the plan's stated childbirth period. If none is stated, the plan's short-term entitlement (V6). A plan whose stages are coded as consecutive components (for example 16 weeks at full pay, then 10 weeks at 60%) is one short-term entitlement. This is reported separately because the 2018 definition excludes these plans (R2).
- **Example:** Old Dominion 2018, birth parent. Sick leave under BOV Policy 1430, up to six months → **26**. Field 1 is 0.
- **Excludes:** childbirth-specific benefits (they are in field 1); long-term disability plans, which are recorded without a length (no childbirth length can come from them).

### 7. Protected weeks (`protected_weeks_max`, with its basis column `protected_basis`)
- **Question:** for how long can a parent be away on job-protected leave because of the birth?
- **Definition:** the longest continuous period of such leave (U3). It covers:
  - the **statutory floor** of the jurisdiction, whether or not the documents name it: FMLA's 12 weeks in the US; the province's employment-standards pregnancy and parental leave in Canada; taken at 2018-01-01 for every 2018 record, including those read against a different row date, and at the collection date for 2026 (`statutory_floor`; U7);
  - other statutory leave the institution's documents rely on (U4; US state laws count only where the documents rely on them);
  - the institution's own maternity, parental and child-care leaves, paid or unpaid, whatever pays them: a leave paid only from the employee's own balances counts here, though its pay counts in no paid figure (U3, R1);
  - leave for the birth parent's own illness or disability (medical or disability leave once paid leave runs out; flag `own_illness_leave`), and leave to care for a seriously ill family member for the non-birth parent (flag `family_illness_leave`) (U5). Both are conditional on a medical finding and count at their stated maximum, but only up to 52 weeks after the birth; the record keeps the stated length. A leave with no stated end that is not only the employee's own illness (a pregnancy or childbirth disability leave, or a medical leave that serves both self and family care) counts to the same 52-week horizon for each parent it serves (flag `open_ended_medical_leave`; U5). The horizon does not apply to leaves that exist because of the birth or adoption, nor to the statutory floor. A paid medical leave of absence for the birth parent's own disability counts as leave (U6); a pay plan that grants no leave does not.

  The leaves are placed in time by their links (R15; a statute alongside the institution's leaves: S1); leaves not joined by any link are not added together, alternatives give the longest, and stated limits cap the total (U3, R20). How an open-ended leave counted to the 52-week horizon is placed in time: U5. A leave counts only for the time the text guarantees return to the job (`job_protected_weeks`, where set; U3). A stated range counts at its lower value (R13b). The figure is never below the floor (U7). The basis column names the leaves and links behind the figure.
- **Example:** Queen's 2018, birth parent. A 20-week maternity leave, with the provincial 17-week pregnancy leave inside it, then the 61-week provincial parental leave → **78**. Basis: `c11[0-17] c1[0-20] c12[17-78] c10[20-72]` (the leaves; the column also lists the paid components placed within them).
- **Example (the floor):** Florida Tech 2018. The documents name no statutory leave, so FMLA's 12 weeks apply → **12**. Basis: `statutory floor[0-12]`.
- **Example (consecutive leaves, statute alongside):** Dartmouth 2018, birth parent. Maternity leave, then parental leave, each one 11-week term, with FMLA from the start → 22; the six-month medical leave for her own disability is longer, so the figure is **26**.
- **Example (leave for own disability):** Clemson 2018, birth parent. Leave for a certified disability due to maternity, up to 180 calendar days, which the agency may not deny → **25.7**.
- **Example (the 52-week horizon):** York 2018. A four-year incapacity leave counts to week 52 (U5).
- **Excludes:**
  - government benefits (they place leaves in time but are not leave);
  - general-purpose leaves (U1);
  - paid relief that keeps research (R4c). So this figure can fall below field 5 where paid weeks include such relief;
  - US state statutes the documents do not rely on (U4);
  - the part of a leave for which the text does not guarantee return to the job (U3).

### 8. Unpaid weeks after paid (`unpaid_weeks_after_paid`)
- **Question:** how much longer is the protected period than the paid period? Where some paid weeks fall outside the protected period (relief that keeps research, R4c), this is not the unpaid part of the protected period.
- **Definition:** field 7 minus field 5, floored at 0 (U3, part b).
- **Example:** Old Dominion 2018, birth parent. No employer-paid leave for faculty; 12 weeks of FMLA leave → protected 12, paid 0 → **12**.
- **Excludes:** as fields 5 and 7.

### Flag columns (published alongside the figures)
- `scope_limits`: leave and relief components limited to part of the faculty, counted or not (V3b).
- `use_limits`: components with a stated limit on how many times they may be used, or for how many children, with their mechanism (U9). The figures describe one use.
- `conditional_refusal`: components granted unless the institution makes a stated finding (V2b, V2d).
- `n_ambiguous_flags`: the number of components flagged `ambiguous`.
- `missing`: whether the figures could not be determined, and why.
- `term_weeks_used`, `term_source`: the term length used to convert terms to weeks, and its source: a stated length (`stated`), the academic calendar (`calendar`), v1.0's term length for the institution (`coding_2018`) or the kind default (`kind_default`) (R8).
