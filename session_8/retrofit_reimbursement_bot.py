"""Session 8 exercise: retrofit logging and exception handling onto a working bot.

This is Session 4's reimbursement bot again — the business logic is already correct
and unchanged. Your job is instrumentation, not new features. Read logging_reference.py
first, then make these four changes (marked TODO below):

1. Set up a module-level `logger` with a console handler (INFO+) and a file handler
   (DEBUG+, writing to bot.log) — same pattern as logging_reference.py.
2. Replace every `print(...)` call with an appropriate `logger` call
   (`.info(...)` for normal progress, `.warning(...)` for a skipped/invalid request).
3. In `main()`'s loop, wrap the `read_request(...)` call in a try/except catching
   `Exception` broadly. On failure: log it with `logger.exception(...)` (captures the
   full traceback), move the file to `errors/` instead of leaving it in `input/`,
   count it as errored, and move on to the next file — one bad file shouldn't crash
   the whole batch.
4. In `ensure_ledger`, wrap the workbook open/create calls in try/except. On failure:
   log it with `logger.exception(...)` and re-raise — unlike a single bad request,
   a broken ledger means nothing else can proceed, so this one should stop the run.

Try running this file as-is first, before making any changes: it will crash
uncaught on request_007.csv (an empty file) — that's the bug TODO 3 fixes, and
it's worth seeing the raw crash before you fix it.

Run: python retrofit_reimbursement_bot.py
Check your work: python check_solution.py
"""
import logging
from pathlib import Path

from RPA.Excel.Files import Files
from RPA.FileSystem import FileSystem
from RPA.Tables import Tables

APPROVAL_THRESHOLD_EUR = 50.00
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
PROCESSED_DIR = BASE_DIR / "processed"
ERRORS_DIR = BASE_DIR / "errors"
LEDGER_PATH = BASE_DIR / "ledger.xlsx"
LOG_PATH = BASE_DIR / "bot.log"

REQUIRED_FIELDS = ["request_id", "member_name", "amount_eur", "category", "date", "description"]
LEDGER_HEADERS = ["date", "member_name", "amount_eur", "category", "description", "status", "source_file"]

logger = logging.getLogger("reimbursement_bot")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

file_handler = logging.FileHandler(LOG_PATH, mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def read_request(csv_path, tables):
    table = tables.read_table_from_csv(str(csv_path), header=True)
    rows, _cols = tables.get_table_dimensions(table)
    if rows != 1:
        logger.warning(
    f"  invalid ({csv_path.name}):"
      f" expected exactly 1 data row, found {rows}"
)
        return None

    row = tables.get_table_row(table, 0, as_list=False)
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            logger.warning(f"  invalid ({csv_path.name}): missing required field {field!r}")
            return None

    try:
        row["amount_eur"] = float(row["amount_eur"])
    except ValueError:
        logger.warning(f"  invalid ({csv_path.name}): amount_eur {row['amount_eur']!r} is not a number")
        return None

    return row


def approval_status(amount_eur):
    if amount_eur <= APPROVAL_THRESHOLD_EUR:
        return "auto-approved"
    return "needs manager approval"

def ensure_ledger(excel):
    try:
        if LEDGER_PATH.exists():
            excel.open_workbook(str(LEDGER_PATH))
        else:
            excel.create_workbook(path=str(LEDGER_PATH), sheet_name="Ledger")
            excel.append_rows_to_worksheet([LEDGER_HEADERS])
            excel.save_workbook()
    except Exception:
        logger.exception("Could not open or create ledger")
        raise


def append_to_ledger(excel, request, status, source_file):
    row = [
        request["date"], request["member_name"], request["amount_eur"],
        request["category"], request["description"], status, source_file,
    ]
    excel.append_rows_to_worksheet([row])


def main():
    fs = FileSystem()
    tables = Tables()
    excel = Files()

    fs.create_directory(str(PROCESSED_DIR), exist_ok=True)
    fs.create_directory(str(ERRORS_DIR), exist_ok=True)
    ensure_ledger(excel)

    csv_files = sorted(Path(INPUT_DIR).glob("*.csv"))
    processed, flagged, skipped, errored = 0, 0, 0, 0

    for csv_path in csv_files:
        logger.info(f"Processing {csv_path.name}...")

        try:
            request = read_request(csv_path, tables)
        except Exception:
            logger.exception(f"Could not read request {csv_path.name}")
            fs.move_file(
                str(csv_path),
                str(ERRORS_DIR / csv_path.name),
                overwrite=True,
            )
            errored += 1
            continue

        if request is None:
            skipped += 1
            continue

        status = approval_status(request["amount_eur"])
        append_to_ledger(excel, request, status, csv_path.name)
        processed += 1
        if status == "needs manager approval":
            flagged += 1
        
        logger.info(f"  {status} ({request['amount_eur']:.2f} EUR)")

        fs.move_file(str(csv_path), str(PROCESSED_DIR / csv_path.name), overwrite=True)

    excel.save_workbook()
    excel.close_workbook()

    
    
    logger.info(f"Processed: {processed}, needs manager approval: {flagged}, "
                f"skipped (invalid): {skipped}, errored: {errored}")


if __name__ == "__main__":
    main()
