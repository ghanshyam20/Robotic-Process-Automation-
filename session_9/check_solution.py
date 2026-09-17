"""Run this after classify_requests.py to check your work.

python check_solution.py
"""
from pathlib import Path

from RPA.Excel.Files import Files

BASE_DIR = Path(__file__).parent
PROCESSED_DIR = BASE_DIR / "processed"
REPORT_PATH = BASE_DIR / "classification_report.xlsx"

EXPECTED_PROCESSED = {
    "request_201.csv", "request_202.csv", "request_203.csv",
    "request_204.csv", "request_205.csv",
}
EXPECTED_RESULTS = {
    "R201": "match",
    "R202": "mismatch",
    "R203": "match",
    "R204": "match",
    "R205": "mismatch",
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
    check("classification_report.xlsx exists", REPORT_PATH.exists())

    if PROCESSED_DIR.exists():
        found = {p.name for p in PROCESSED_DIR.glob("*.csv")}
        check(f"processed/ contains all 5 requests (found {sorted(found)})",
              found == EXPECTED_PROCESSED)
    else:
        check("processed/ directory exists", False)

    if REPORT_PATH.exists():
        excel = Files()
        excel.open_workbook(str(REPORT_PATH))
        rows = excel.read_worksheet(header=True)
        excel.close_workbook()

        check(f"report has exactly 5 rows (found {len(rows)})", len(rows) == 5)

        by_id = {row.get("request_id"): row for row in rows}
        for request_id, expected_result in EXPECTED_RESULTS.items():
            row = by_id.get(request_id)
            check(f"{request_id}: result == {expected_result!r} (llm_category populated)",
                  row is not None and row.get("result") == expected_result
                  and bool(row.get("llm_category")))

    print()
    print(f"{checks_passed}/{checks_total} checks passed")
    print()
    print("Note: this checks against llama3.1:8b's actual output at temperature=0. If your "
          "Ollama model differs or has been updated, a mismatch here doesn't necessarily mean "
          "your code is wrong — see notes.md.")


if __name__ == "__main__":
    main()
