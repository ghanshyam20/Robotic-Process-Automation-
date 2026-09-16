"""Session 4 exercise: process new expense-reimbursement requests.

Fill in the three TODO functions below. Everything else (directory setup, the
ledger workbook, the main loop) is already wired up and calls your functions —
don't change their signatures. Run: python process_reimbursements.py
Check your work: python check_solution.py

This is the same club-expense-reimbursement process you wrote a PDD for in
Session 3 — APPROVAL_THRESHOLD_EUR below is that PDD's business rule.
"""
from pathlib import Path

from RPA.Excel.Files import Files
from RPA.FileSystem import FileSystem
from RPA.Tables import Tables

APPROVAL_THRESHOLD_EUR = 50.00
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
PROCESSED_DIR = BASE_DIR / "processed"
LEDGER_PATH = BASE_DIR / "ledger.xlsx"

REQUIRED_FIELDS = ["request_id", "member_name", "amount_eur", "category", "date", "description"]
LEDGER_HEADERS = ["date", "member_name", "amount_eur", "category", "description", "status", "source_file"]


def read_request(csv_path, tables):
    """Read one request CSV. Return it as a dict, or None if invalid.
    

    TODO:
    1. Use `tables.read_table_from_csv(str(csv_path), header=True)` to read the file
       into a Table (see RPA.Tables — this is the library from Session 3's PDD lecture
       on candidate criteria, now put to use).
    2. Use `tables.get_table_dimensions(table)` to check there's exactly one data row.
       If not, print a short reason and return None — this is an *application*
       exception (Session 3, slide 4): something's wrong with the input itself.
    3. Use `tables.get_table_row(table, 0, as_list=False)` to get the row as a dict.
    4. Check every field in REQUIRED_FIELDS is present and non-empty. If one is
       missing, print why and return None.
    5. Convert row["amount_eur"] to a float. If that fails (ValueError), print why
       and return None.
    6. Return the row dict (with amount_eur now a float).
    """
    table=tables.read_table_from_csv(str(csv_path),header=True)

    rows,_=tables.get_table_dimensions(table)
    if rows!=1:
        print(f"Invalid:Expected exactly one data row found{rows}")
        return None

    row=tables.get_table_row(table,0,as_list=False)

    for field in REQUIRED_FIELDS:
        if field not in row or row[field] is None or str(row[field].strip())=="":
            print(f"Invalid: Field '{field}' is missing or empty")
            return None

    try:
        row["amount_eur"] = float(row["amount_eur"])
        
    except ValueError:
        print("Invalid: amount_eur is not a valid number")
        return None

    if row["amount_eur"]<=0:
        print("Invalid:amount_eur must be greater than zero")
        return None

    return row


def approval_status(amount_eur):
    """TODO: apply Session 3's PDD business rule.

    Return "auto-approved" if amount_eur is at or below APPROVAL_THRESHOLD_EUR,
    otherwise return "needs manager approval". This is a *business* exception
    (Session 3, slide 4): a valid, expected branch — not a failure.
    """
    if amount_eur<=APPROVAL_THRESHOLD_EUR:
        return "auto-approved"
    return "needs manager approval"


def append_to_ledger(excel, request, status, source_file):
    """TODO: append one row to the ledger workbook.

    Build a list matching LEDGER_HEADERS's order: date, member_name, amount_eur,
    category, description, status, source_file — pull the first five from `request`,
    and use the `status` and `source_file` arguments for the last two.
    Call `excel.append_rows_to_worksheet([your_row])` to write it (note the row
    needs to be wrapped in a list — the method appends *rows*, plural).
    """
    row = [
        request["date"],
        request["member_name"],
        request["amount_eur"],
        request["category"],
        request["description"],
        status,
        source_file
    ]
    excel.append_rows_to_worksheet([row])


def ensure_ledger(excel):
    """Given: opens the ledger if it exists, or creates it with a header row."""
    if LEDGER_PATH.exists():
        excel.open_workbook(str(LEDGER_PATH))
    else:
        excel.create_workbook(path=str(LEDGER_PATH), sheet_name="Ledger")
        excel.append_rows_to_worksheet([LEDGER_HEADERS])
        excel.save_workbook()


def main():
    fs = FileSystem()
    tables = Tables()
    excel = Files()

    fs.create_directory(str(PROCESSED_DIR), exist_ok=True)
    ensure_ledger(excel)

    csv_files = sorted(Path(INPUT_DIR).glob("*.csv"))
    processed, flagged, skipped = 0, 0, 0

    for csv_path in csv_files:
        print(f"Processing {csv_path.name}...")
        request = read_request(csv_path, tables)
        if request is None:
            skipped += 1
            continue

        status = approval_status(request["amount_eur"])
        append_to_ledger(excel, request, status, csv_path.name)
        processed += 1
        if status == "needs manager approval":
            flagged += 1
        print(f"  {status} ({request['amount_eur']:.2f} EUR)")

        fs.move_file(str(csv_path), str(PROCESSED_DIR / csv_path.name), overwrite=True)

    excel.save_workbook()
    excel.close_workbook()

    print()
    print(f"Processed: {processed}, needs manager approval: {flagged}, skipped (invalid): {skipped}")


if __name__ == "__main__":
    main()
