"""Check that the released data files are reproduced exactly from the released records, reference tables and code.

Usage (from the version folder, data/2018/v2.0/):
    python code/test_rebuild.py

Rebuilds the data set CSV, the v1/v2 differences file and the website's timeline data into a temporary folder and compares them byte for byte with the released copies, and checks every record's
statutory floor against the baseline table. Exits 0 when all match.

Released under the BSD 3-Clause license (see LICENSE-CODE).
"""
import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = ROOT / "code"
TARGETS = [("build_csv.py", ROOT / "parental_leave_2018_v2.0.csv"),
           ("build_differences.py", ROOT / "v1_v2_differences.csv"),
           ("build_site_data.py", ROOT / "timelines.json")]


def main():
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for script, released in TARGETS:
            rebuilt = Path(tmp) / released.name
            # the differences are computed from the released CSV, which the first check confirms
            subprocess.run([sys.executable, str(CODE / script), "--out", str(rebuilt)], check=True, cwd=ROOT,
                           stdout=subprocess.DEVNULL)
            same = filecmp.cmp(rebuilt, released, shallow=False)
            print(f"{'OK  ' if same else 'DIFF'} {released.relative_to(ROOT)}")
            failed += not same
    # every record's statutory floor is the one the baseline table gives (U7)
    floor = subprocess.run([sys.executable, str(CODE / "statutory_floor.py")], cwd=ROOT, capture_output=True, text=True)
    print(f"{'OK  ' if floor.returncode == 0 else 'DIFF'} records' statutory_floor against reference/statutory_baseline.csv")
    failed += floor.returncode != 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
