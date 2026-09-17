"""Run this after hybrid_extract.py to check your work.

python check_solution.py
"""
from pathlib import Path

from RPA.Excel.Files import Files

BASE_DIR = Path(__file__).parent
PROCESSED_DIR = BASE_DIR / "processed"
NEEDS_REVIEW_DIR = BASE_DIR / "needs_review"
REPORT_PATH = BASE_DIR / "extraction_report.xlsx"

EXPECTED_PROCESSED = {"receipt_001.png", "receipt_002.png"}
EXPECTED_NEEDS_REVIEW = {"receipt_003.png"}
EXPECTED_REGEX_ROWS = {
    "receipt_001.png": {"vendor": "PARTSKESKUS OY", "date": "2026-09-02", "amount_eur": 17.4},
    "receipt_002.png": {"vendor": "KILTA KAHVILA", "date": "2026-09-10", "amount_eur": 75.0},
}

checks_passed = 0
checks_total = 0


def check(label, condition):
    global checks_passed, checks_total
    checks_total += 1
    status = "PASS" if condition else "FAIL"
    if condition:
        checks_passed += 1
    print(f"[{status}] {label}")


def main():
    check("extraction_report.xlsx exists", REPORT_PATH.exists())

    if PROCESSED_DIR.exists():
        found = {p.name for p in PROCESSED_DIR.glob("*.png")}
        check(f"processed/ contains the 2 regex-extractable receipts (found {sorted(found)})",
              found == EXPECTED_PROCESSED)
    else:
        check("processed/ directory exists", False)

    if NEEDS_REVIEW_DIR.exists():
        found = {p.name for p in NEEDS_REVIEW_DIR.glob("*.png")}
        check(f"needs_review/ contains the hard-to-OCR receipt (found {sorted(found)})",
              found == EXPECTED_NEEDS_REVIEW)
    else:
        check("needs_review/ directory exists", False)

    if not REPORT_PATH.exists():
        print(f"\n{checks_passed}/{checks_total} checks passed")
        return

    excel = Files()
    excel.open_workbook(str(REPORT_PATH))
    rows = excel.read_worksheet(header=True)
    excel.close_workbook()

    check(f"report has exactly 3 rows (found {len(rows)})", len(rows) == 3)
    by_file = {row.get("source_file"): row for row in rows}

    for fname, expected in EXPECTED_REGEX_ROWS.items():
        row = by_file.get(fname)
        ok = (row is not None
              and row.get("vendor") == expected["vendor"]
              and row.get("date") == expected["date"]
              and float(row.get("amount_eur", -1)) == expected["amount_eur"]
              and row.get("extraction_method") == "regex"
              and row.get("needs_review") in (False, "False", 0))
        check(f"{fname}: extracted via regex with exact expected values", ok)

    hard_row = by_file.get("receipt_003.png")
    # Deliberately NOT checking the exact amount here: the LLM fallback's numeric
    # answer is model-dependent (see notes.md/exercise-solution/README.md for why) —
    # what matters is that the fallback ran, produced *something* for every field,
    # and is correctly flagged for a human to check.
    ok = (hard_row is not None
          and hard_row.get("extraction_method") == "llm"
          and hard_row.get("needs_review") in (True, "True", 1)
          and hard_row.get("vendor") and hard_row.get("date")
          and hard_row.get("amount_eur") not in (None, ""))
    check("receipt_003.png: LLM fallback ran, populated every field, flagged needs_review", ok)

    print()
    print(f"{checks_passed}/{checks_total} checks passed")


if __name__ == "__main__":
    main()
