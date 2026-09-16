"""Run this after retrofit_reimbursement_bot.py to check your work.

python check_solution.py
"""
from pathlib import Path

from RPA.Excel.Files import Files

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
PROCESSED_DIR = BASE_DIR / "processed"
ERRORS_DIR = BASE_DIR / "errors"
LEDGER_PATH = BASE_DIR / "ledger.xlsx"
LOG_PATH = BASE_DIR / "bot.log"

EXPECTED_PROCESSED = {
    "request_001.csv", "request_002.csv", "request_003.csv",
    "request_004.csv", "request_006.csv",
}
EXPECTED_ERRORS = {"request_007.csv"}
EXPECTED_STILL_IN_INPUT = {"request_005.csv"}

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
    check("ledger.xlsx exists", LEDGER_PATH.exists())
    check("bot.log exists", LOG_PATH.exists())

    if PROCESSED_DIR.exists():
        found = {p.name for p in PROCESSED_DIR.glob("*.csv")}
        check(f"processed/ contains the 5 valid requests (found {sorted(found)})",
              found == EXPECTED_PROCESSED)
    else:
        check("processed/ directory exists", False)

    if ERRORS_DIR.exists():
        found = {p.name for p in ERRORS_DIR.glob("*.csv")}
        check(f"errors/ contains the unreadable request (found {sorted(found)})",
              found == EXPECTED_ERRORS)
    else:
        check("errors/ directory exists", False)

    if INPUT_DIR.exists():
        remaining = {p.name for p in INPUT_DIR.glob("*.csv")}
        check(f"input/ still has only the invalid request (found {sorted(remaining)})",
              remaining == EXPECTED_STILL_IN_INPUT)

    if LEDGER_PATH.exists():
        excel = Files()
        excel.open_workbook(str(LEDGER_PATH))
        rows = excel.read_worksheet(header=True)
        excel.close_workbook()
        check(f"ledger has exactly 5 rows (found {len(rows)})", len(rows) == 5)

    if LOG_PATH.exists():
        log_text = LOG_PATH.read_text()
        check("log file has a WARNING for the invalid request",
              "WARNING" in log_text and "request_005.csv" in log_text)
        check("log file has an ERROR (with traceback) for the unreadable request",
              "ERROR" in log_text and "request_007.csv" in log_text and "Traceback" in log_text)
        check("log file has INFO lines for successfully processed requests",
              log_text.count("INFO") >= 5)

    print()
    print(f"{checks_passed}/{checks_total} checks passed")


if __name__ == "__main__":
    main()
