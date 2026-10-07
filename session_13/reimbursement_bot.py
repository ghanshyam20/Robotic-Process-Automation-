"""Given — Session 8's bot, unchanged, carried forward as this session's test
target. Nothing to implement here; this is what test_bot.py tests and what
produces the bot.log that monitor.py reads. Run: python reimbursement_bot.py
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
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def read_request(csv_path, tables):
    table = tables.read_table_from_csv(str(csv_path), header=True)
    rows, _cols = tables.get_table_dimensions(table)
    if rows != 1:
        logger.warning("%s: expected exactly 1 data row, found %d", csv_path.name, rows)
        return None

    row = tables.get_table_row(table, 0, as_list=False)
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            logger.warning("%s: missing required field %r", csv_path.name, field)
            return None

    try:
        row["amount_eur"] = float(row["amount_eur"])
    except ValueError:
        logger.warning("%s: amount_eur %r is not a number", csv_path.name, row["amount_eur"])
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
        logger.exception("Could not open or create the ledger workbook — cannot continue")
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
        logger.debug("Processing %s", csv_path.name)

        try:
            request = read_request(csv_path, tables)
        except Exception:
            logger.exception("Unexpected error reading %s — moving to errors/", csv_path.name)
            fs.move_file(str(csv_path), str(ERRORS_DIR / csv_path.name), overwrite=True)
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
        logger.info("%s: %s (%.2f EUR)", csv_path.name, status, request["amount_eur"])

        fs.move_file(str(csv_path), str(PROCESSED_DIR / csv_path.name), overwrite=True)

    excel.save_workbook()
    excel.close_workbook()

    logger.info(
        "Processed: %d, needs manager approval: %d, skipped (invalid): %d, errored: %d",
        processed, flagged, skipped, errored,
    )


if __name__ == "__main__":
    main()
