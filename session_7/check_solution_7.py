"""Run this after extract_receipts.py to check your work.

python check_solution.py
"""
from pathlib import Path

from RPA.Excel.Files import Files

BASE_DIR = Path(__file__).parent
RECEIPTS_DIR = BASE_DIR / "receipts"
PROCESSED_DIR = BASE_DIR / "processed"
NEEDS_REVIEW_DIR = BASE_DIR / "needs_review"
LEDGER_PATH = BASE_DIR / "receipts_ledger.xlsx"

EXPECTED_PROCESSED = {"receipt_001.png", "receipt_002.png"}
EXPECTED_NEEDS_REVIEW = {"receipt_003.png"}
EXPECTED_ROWS = {
    "receipt_001.png": {"vendor": "PARTSKESKUS OY", "date": "2026-09-02", "amount_eur": 17.4, "status": "auto-approved"},
    "receipt_002.png": {"vendor": "KILTA KAHVILA", "date": "2026-09-10", "amount_eur": 75.0, "status": "needs manager approval"},
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
    check("receipts_ledger.xlsx exists", LEDGER_PATH.exists())
    check("processed/ directory exists", PROCESSED_DIR.exists())
    check("needs_review/ directory exists", NEEDS_REVIEW_DIR.exists())

    if PROCESSED_DIR.exists():
        found = {p.name for p in PROCESSED_DIR.glob("*.png")}
        check(f"processed/ contains the 2 clean receipts (found {sorted(found)})",
              found == EXPECTED_PROCESSED)

    if NEEDS_REVIEW_DIR.exists():
        found = {p.name for p in NEEDS_REVIEW_DIR.glob("*.png")}
        check(f"needs_review/ contains the unreadable receipt (found {sorted(found)})",
              found == EXPECTED_NEEDS_REVIEW)

    if LEDGER_PATH.exists():
        excel = Files()
        excel.open_workbook(str(LEDGER_PATH))
        rows = excel.read_worksheet(header=True)
        excel.close_workbook()

        check(f"ledger has exactly 2 rows (found {len(rows)})", len(rows) == 2)

        def field_matches(key, actual, expected):
            if key == "amount_eur":
                try:
                    return float(actual) == float(expected)
                except (TypeError, ValueError):
                    return False
            return str(actual) == str(expected)

        by_file = {row.get("source_file"): row for row in rows}
        for fname, expected in EXPECTED_ROWS.items():
            row = by_file.get(fname)
            ok = row is not None and all(field_matches(k, row.get(k), v) for k, v in expected.items())
            check(f"{fname}: {expected}", ok)

    print()
    print(f"{checks_passed}/{checks_total} checks passed")


if __name__ == "__main__":
    main()
