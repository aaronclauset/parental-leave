"""List the release's principal files with their sizes, for the release notes.

Usage (from the version folder, data/2018/v2.0/):
    python code/build_manifest.py [--out files.json]

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "files.json"
FILES = ["parental_leave_2018_v2.0.csv", "DATA_DICTIONARY.md", "v1_v2_differences.csv",
         "provenance/index.csv", "reference/institutions.csv", "reference/component_tiers.csv",
         "reference/calendar_2017_18.csv", "reference/statutory_baseline.csv", "reference/programs.csv",
         "reference/aau_members_2018.csv", "reference/prestige_wapman.csv", "reference/v1_v2_causes.csv"]
FOLDERS = ["records", "guidance", "code"]


def size(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB" if n >= 1e3 else f"{n} B"


def build(out):
    files = []
    for f in FILES:
        p = ROOT / f
        files.append({"path": f, "size": size(p.stat().st_size)})
    for d in FOLDERS:
        paths = sorted(p for p in (ROOT / d).iterdir() if p.is_file() and not p.name.startswith("."))
        files.append({"path": d + "/", "size": f"{len(paths)} files, {size(sum(p.stat().st_size for p in paths))}"})
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"files": files}, f, indent=1)
        f.write("\n")
    print(f"wrote {len(files)} entries to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    build(ap.parse_args().out)
