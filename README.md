<p align="center"><img src="assets/logo_green.png" width="140" alt="The Faculty Parental Leave Project logo"></p>

# The Faculty Parental Leave Project

The Faculty Parental Leave Project aims to measure, track, and understand the parental-leave benefits that universities provide to faculty. Parenthood is among the most impactful events in a faculty career, and that impact can vary broadly across individuals and across institutions. This project aims to measure that variability, identify patterns in leave benefits, and understand how parenthood is changing for faculty.

Parental leave policies are often complicated, and many faculty are not aware of the benefits their own university provides. The project systematically collects and analyzes these policies, and provides open data for researchers to use to better understand how parenthood impacts academic careers.

**Website:** https://aaronclauset.github.io/parental-leave/ — highlights from the data, an interactive explorer, every institution's policy as a benefits timeline, and the release notes.

**Update, November 2026:** a new version of the 2018 data (v2.0) is available. It re-collects the policies of the same 205 universities from each institution's own policy documents, and adds measures of pay and job protection.

## Data sets
Each data set is a sample of institutions, measured at one point in time. Each released version has its own folder, `data/<sample>/v<version>/`, which holds everything needed to use and rebuild it.

| Sample | Version | Released | Institutions | Files |
|---|---|---|---|---|
| 2018 | **v2.0** (current) | November 2026 | 205 | `data/2018/v2.0/` |
| 2018 | v1.0 | April 2018, corrected to January 2019 | 205 | `data/2018/v1.0/` |

The 2018 sample covers tenured and tenure-track faculty at 205 research universities in the United States and Canada with PhD-granting computer science departments, with the policies in force in the 2017–18 academic year. Version 1.0 was published with Morgan et al. (2018); the root file `parental_leave_policies.tsv` is the same file, kept for existing links. How v2.0 differs from v1.0, institution by institution: the [release notes](https://aaronclauset.github.io/parental-leave/release-notes/2018-v2.0.html) and `data/2018/v2.0/v1_v2_differences.csv`. The 2018 website that presented v1.0 is archived in `archive/2018-v1.0/` ([view it](https://aaronclauset.github.io/parental-leave/archive/2018-v1.0/)).

## What the data measure
Parental leave benefits typically come in two forms. A **leave** is time away from all duties, often paid. **Relief** (or modified duties) keeps the faculty member employed at full pay while removing some duties, usually teaching. The **primary value** measures, for each parent, the number of weeks of employer-paid leave or of full-pay relief, whichever is longer. Each value is recorded for the **birth parent** and the **non-birth parent**, both as **guaranteed** and **with discretionary benefits**. Secondary values describe pay and job protection more broadly. Every column is defined in `data/2018/v2.0/DATA_DICTIONARY.md`.

For v2.0, policy discovery, collection, and extraction were automated using a structured pipeline of large language models (Claude) and deterministic code. Models found each institution's documents, read them and encoded each policy as a set of components, each coded field paired with a verbatim quote from the source. Deterministic code then checked every record and computed every value. Questions the coding rules did not settle were decided by the research team and written into the rules. The website's "Data collection protocol" section describes each step and the limitations.

## What is in this repository
The 2018 v2.0 release, in `data/2018/v2.0/`:

| Path | Content |
|---|---|
| `parental_leave_2018_v2.0.csv` | The 2018 v2.0 data set, one row per institution |
| `DATA_DICTIONARY.md` | Every column of the data set |
| `v1_v2_differences.csv` | v1.0 and v2.0 values side by side, with the cause of each difference |
| `records/` | The structured encoding of each institution's policy (JSON), with the verbatim quote supporting every coded field |
| `guidance/` | The coding rules, schema, checklist, field meanings and reader instructions |
| `provenance/index.csv` | Every source document, with its URL, web-archive capture, retrieval date and SHA-256 |
| `reference/` | Institution metadata, statutory baselines, government programs, 2017–18 calendar term lengths, AAU membership, the prestige crosswalk, component tiers |
| `code/` | The code that rebuilds every data file from the encodings |
| `timelines.json`, `files.json` | The component timelines the website's policy viewer draws, and the file list of the release notes |

Elsewhere in the repository:

| Path | Content |
|---|---|
| `data/2018/v1.0/` | The 2018 v1.0 data set, unchanged |
| `index.html`, `release-notes/`, `assets/` | The website |
| `archive/2018-v1.0/` | The 2018 website, kept as it was: the original home page, the interactive policy page, and the comparison with the technology industry (with `tech.tsv` and the `python/` notebook) |
| `parental_leave_policies.tsv` | The v1.0 data set at its original path, for existing links |

## Reproducing the data
With Python 3.9 or later (standard library only), from the version's folder:

```
cd data/2018/v2.0
python code/test_rebuild.py
```

This rebuilds the data set, the differences file and the website's timeline data from `records/` and `reference/` (and the v1.0 file in `data/2018/v1.0/`), and checks them byte for byte against the released files. `code/REPRODUCE.md` describes each step. The source documents themselves are not distributed; `provenance/index.csv` identifies each one by its URL and web-archive capture.

## License
- **Data, encodings, guidance and reference tables** (both versions): Creative Commons Attribution 4.0 International (CC BY 4.0); see `LICENSE`.
- **Code:** BSD 3-Clause; see `LICENSE-CODE`.
- The verbatim quotes in the encodings are short excerpts of documents whose copyright remains with their owners; see `SOURCES_NOTICE.md`.

## How to cite
- **Version 2.0:** A. Clauset, "Faculty parental-leave policies at U.S. and Canadian universities, 2018 v2.0" (2026). https://github.com/aaronclauset/parental-leave
- **Version 1.0:** A. C. Morgan, S. F. Way, M. Galesic, D. B. Larremore and A. Clauset, "Paid parental leave at US and Canadian universities" (2018).

## About us
The Faculty Parental Leave Project is based at the University of Colorado Boulder. Its contributors are [Allison C. Morgan](https://allisonmorgan.github.io), [Samuel F. Way](http://samfway.com), [Michael J. D. Hoefer](https://www.michaelhoefer.com), [Daniel B. Larremore](https://larremorelab.github.io/dan), [Mirta Galesic](https://sites.google.com/site/mirtagalesic/) and [Aaron Clauset](https://aaronclauset.github.io).

**Publication:** A. C. Morgan, S. F. Way, M. J. D. Hoefer, D. B. Larremore, M. Galesic and A. Clauset, "The unequal impact of parenthood in academia." *Science Advances* 7(9), eabd1996 (2021). [doi:10.1126/sciadv.abd1996](https://doi.org/10.1126/sciadv.abd1996)

**Funding:** supported in part by the National Science Foundation (award SMA 1633791), the Air Force Office of Scientific Research (award FA9550-19-1-0329), and a National Science Foundation Graduate Research Fellowship (award DGE 1650115).
