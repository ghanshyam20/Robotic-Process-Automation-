"""Run this after scrape_inventory.py to check your work.

python check_solution.py
"""
from pathlib import Path

from RPA.Excel.Files import Files

BASE_DIR = Path(__file__).parent
REPORT_PATH = BASE_DIR / "needs_repair_report.xlsx"

EXPECTED_ROWS = [
    {"item": "3D Printer", "category": "Robotics Kits", "quantity": 1, "status": "Needs Repair"},
    {"item": "Cordless Drill", "category": "Tools", "quantity": 3, "status": "Needs Repair"},
    {"item": "Competition Drone", "category": "Robotics Kits", "quantity": 1, "status": "Needs Repair"},
]

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
    check("needs_repair_report.xlsx exists", REPORT_PATH.exists())
    if not REPORT_PATH.exists():
        print(f"\n{checks_passed}/{checks_total} checks passed")
        return

    excel = Files()
    excel.open_workbook(str(REPORT_PATH))
    rows = excel.read_worksheet(header=True)
    excel.close_workbook()

    check(f"report has exactly 3 rows (found {len(rows)})", len(rows) == 3)

    by_item = {row.get("item"): row for row in rows}
    for expected in EXPECTED_ROWS:
        row = by_item.get(expected["item"])
        ok = row is not None and all(str(row.get(k)) == str(v) for k, v in expected.items())
        check(f"{expected['item']}: {expected}", ok)

    print()
    print(f"{checks_passed}/{checks_total} checks passed")


if __name__ == "__main__":
    main()
