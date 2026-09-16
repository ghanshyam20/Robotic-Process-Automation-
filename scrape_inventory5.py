"""Session 5 exercise: scrape the club equipment inventory demo page.

Fill in the two TODO functions below. Everything else (browser launch, the
filtering interactions, the main flow) is already wired up and calls your
functions — don't change their signatures.
Run: python scrape_inventory.py
Check your work: python check_solution.py

The site is site/inventory.html, opened directly as a local file — no server
needed. Open it in your own browser first and play with the filters before
writing any code; you're about to automate exactly what you just did by hand.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright
from RPA.Excel.Files import Files

BASE_DIR = Path(__file__).parent
SITE_URL = (BASE_DIR / "site" / "inventory.html").resolve().as_uri()
REPORT_PATH = BASE_DIR / "needs_repair_report.xlsx"
REPORT_HEADERS = ["item", "category", "quantity", "status"]


def extract_visible_rows(page):
    """TODO: return a list of dicts, one per *visible* inventory row.

    The table's rows live under `#inventory-body`. Rows that are currently
    filtered out have a `hidden` attribute — a locator for
    "#inventory-body tr:not([hidden])" selects only the visible ones.

    For each visible row:
    1. Get its four <td> cells with `row.locator("td")`.
    2. Read each cell's text with `.nth(i).text_content()` (0=item, 1=category,
       2=quantity, 3=status) — remember to `.strip()` the text.
    3. Convert quantity to an int.
    4. Build a dict: {"item": ..., "category": ..., "quantity": ..., "status": ...}

    Use `rows.count()` (where `rows` is your locator) to know how many rows to loop over.
    """
    result = []
    rows = page.locator("#inventory-body tr:not([hidden])")

    for i in range(rows.count()):
        row = rows.nth(i)
        cells = row.locator("td")

        item = cells.nth(0).text_content().strip()
        category = cells.nth(1).text_content().strip()
        quantity = int(cells.nth(2).text_content().strip())
        status = cells.nth(3).text_content().strip()

        result.append({
            "item": item,
            "category": category,
            "quantity": quantity,
            "status": status,
        })

    return result


def write_report(rows):
    """TODO: write `rows` to an Excel report, one row per dict, matching
    REPORT_HEADERS's column order.

    This is the same RPA.Excel.Files pattern from Session 4:
    1. `excel = Files()`
    2. `excel.create_workbook(path=str(REPORT_PATH), sheet_name="Needs Repair")`
    3. Append the header row: `excel.append_rows_to_worksheet([REPORT_HEADERS])`
    4. For each row dict, append its values in REPORT_HEADERS's order (wrapped
       in a list, since the method appends *rows*, plural — same gotcha as
       Session 4).
    5. `excel.save_workbook()` then `excel.close_workbook()`
    """
    excel = Files()
    excel.create_workbook(
        path=str(REPORT_PATH),
        sheet_name="Needs Repair"
    )

    excel.append_rows_to_worksheet([REPORT_HEADERS])

    for row in rows:
        report_row = [
            row["item"],
            row["category"],
            row["quantity"],
            row["status"],
        ]
        excel.append_rows_to_worksheet([report_row])

    excel.save_workbook()
    excel.close_workbook()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(SITE_URL)

        # Interaction 1: filter by category, confirm the count updates
        page.fill("#category-filter", "Robotics Kits")
        page.wait_for_selector("text=Showing 4 of 14 items")

        # Interaction 2: clear filters, then filter by status instead
        page.click("#clear-filters")
        page.select_option("#status-filter", "Needs Repair")
        page.wait_for_selector("text=Showing 3 of 14 items")

        rows = extract_visible_rows(page)
        browser.close()

    write_report(rows)
    print(f"Wrote {len(rows)} rows to {REPORT_PATH.name}")
    for row in rows:
        print(" ", row)


if __name__ == "__main__":
    main()
