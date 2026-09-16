"""Session 7 exercise: OCR club expense receipts and log them.

Fill in the one TODO function: `parse_receipt_text`. Everything else (OCR-ing
each image, the approval-threshold rule from Session 3/4, the ledger, moving
files) is given. Run: python extract_receipts.py
Check your work: python check_solution.py

receipts/ has 3 sample receipt images — two clean, one deliberately hard to
read (low contrast, slightly rotated, a bit of scan noise). Open all three in
an image viewer before writing any code, and look at what Tesseract actually
produces for each — try this in a Python REPL:

    import pytesseract
    from PIL import Image
    print(pytesseract.image_to_string(Image.open("receipts/receipt_003.png")))

That garbled output is the input your parsing function has to survive.
"""
import re
from pathlib import Path

import pytesseract
from PIL import Image
from RPA.FileSystem import FileSystem
from RPA.Excel.Files import Files

APPROVAL_THRESHOLD_EUR = 50.00
BASE_DIR = Path(__file__).parent
RECEIPTS_DIR = BASE_DIR / "receipts"
PROCESSED_DIR = BASE_DIR / "processed"
NEEDS_REVIEW_DIR = BASE_DIR / "needs_review"
LEDGER_PATH = BASE_DIR / "receipts_ledger.xlsx"
LEDGER_HEADERS = ["source_file", "vendor", "date", "amount_eur", "status"]

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
TOTAL_PATTERN = re.compile(r"TOTAL.*?(\d+\.\d{2})", re.IGNORECASE)


def parse_receipt_text(text):
    """TODO: parse raw OCR text into {"vendor": ..., "date": ..., "amount_eur": ...},
    or return None if the text isn't usable enough to extract all three fields.

    1. Split `text` into non-empty, stripped lines. If there are none, return None.
    2. Vendor: the receipt's shop name is always the first line — take `lines[0]`.
       (We're not validating that it's correct, just that something is there.)
    3. Date: search the *whole text* (not just one line) with `DATE_PATTERN`
       (already defined above, matches YYYY-MM-DD). If there's no match, return
       None — a receipt without a readable date can't be logged.
    4. Amount: search the whole text with `TOTAL_PATTERN` (matches a line
       containing "TOTAL" followed later by a number like `12.50`). If there's
       no match, return None. Otherwise convert the matched group to a float
       (`.group(1)`, then `float(...)`).
    5. Return the dict with all three fields.

    Why return None instead of guessing: a receipt Tesseract garbled badly
    enough that TOTAL_PATTERN can't find a number is exactly the case this
    exercise routes to needs_review/ instead of the ledger — see main() below.
    Silently logging a wrong amount would be worse than flagging it for a
    human to check.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    vendor = lines[0]

    date_match = DATE_PATTERN.search(text)
    if date_match is None:
        return None

    total_match = TOTAL_PATTERN.search(text)
    if total_match is None:
        return None

    amount = float(total_match.group(1))

    return {
        "vendor": vendor,
        "date": date_match.group(0),
        "amount_eur": amount,
    }


  


def approval_status(amount_eur):
    if amount_eur <= APPROVAL_THRESHOLD_EUR:
        return "auto-approved"
    return "needs manager approval"


def ensure_ledger(excel):
    if LEDGER_PATH.exists():
        excel.open_workbook(str(LEDGER_PATH))
    else:
        excel.create_workbook(path=str(LEDGER_PATH), sheet_name="Receipts")
        excel.append_rows_to_worksheet([LEDGER_HEADERS])
        excel.save_workbook()


def main():
    fs = FileSystem()
    excel = Files()

    fs.create_directory(str(PROCESSED_DIR), exist_ok=True)
    fs.create_directory(str(NEEDS_REVIEW_DIR), exist_ok=True)
    ensure_ledger(excel)

    image_paths = sorted(RECEIPTS_DIR.glob("*.png"))
    processed, needs_review = 0, 0

    for image_path in image_paths:
        print(f"OCR-ing {image_path.name}...")
        text = pytesseract.image_to_string(Image.open(image_path))
        receipt = parse_receipt_text(text)

        if receipt is None:
            print(f"  could not extract vendor/date/amount — needs manual review")
            fs.move_file(str(image_path), str(NEEDS_REVIEW_DIR / image_path.name), overwrite=True)
            needs_review += 1
            continue

        status = approval_status(receipt["amount_eur"])
        row = [image_path.name, receipt["vendor"], receipt["date"], receipt["amount_eur"], status]
        excel.append_rows_to_worksheet([row])
        print(f"  {receipt['vendor']} / {receipt['date']} / {receipt['amount_eur']:.2f} EUR -> {status}")
        fs.move_file(str(image_path), str(PROCESSED_DIR / image_path.name), overwrite=True)
        processed += 1

    excel.save_workbook()
    excel.close_workbook()

    print()
    print(f"Processed: {processed}, needs review: {needs_review}")


if __name__ == "__main__":
    main()
