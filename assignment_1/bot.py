"""Assignment 1 starter — adapt this structure to YOUR chosen process.

This mirrors the pattern from Sessions 4-8: read input -> decide/interact -> extract
via OCR -> handle errors -> log -> write output -> archive. You don't have to keep
this exact shape or order — adapt it to what your process (from your Session 3 PDD)
actually needs. But per spec.md, your submission must include all of:
  - reading input from a file (or a generated work queue)
  - at least one Playwright web interaction
  - at least one OCR extraction from a scanned/image document
  - graceful error handling (no unhandled crashes on expected failure cases) + logging

Fill in each TODO. Delete the parts of this skeleton that don't apply to your process
and add what you need — this is a starting structure, not a rigid template.
"""
import re
import csv
import logging
from pathlib import Path
import pytesseract
from PIL import Image, UnidentifiedImageError
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).parent
LOG_PATH = BASE_DIR / "bot.log"

INPUT_PATH = BASE_DIR / "requests.csv"
SITE_URL = (BASE_DIR / "site" / "reimbursement.html").resolve().as_uri()

REQUIRED_FIELDS = (
    "request_id",
    "member_name",
    "purpose",
    "claimed_amount",
    "receipt_file",
)


OUTPUT_PATH = BASE_DIR / "output" / "results.csv"
RESULT_FIELDS = (
    "request_id",
    "member_name",
    "purpose",
    "claimed_amount",
    "receipt_vendor",
    "receipt_date",
    "receipt_amount",
    "status",
    "confirmation",
    "note",
)

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
AMOUNT_PATTERN = re.compile(r"\d+[.,]\d{2}")


# Same logger pattern as Session 8: a named logger, console handler for a short live
# view (INFO+), file handler for the full record (DEBUG+). Reuse this as-is.
logger = logging.getLogger("assignment1_bot")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

file_handler = logging.FileHandler(LOG_PATH, mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)



def read_input():
    """Read and validate reimbursement requests from the CSV work queue."""

    if not INPUT_PATH.exists():
        logger.error("Input file does not exist: %s", INPUT_PATH)
        return []

    items = []
    seen_request_ids = set()

    try:
        with INPUT_PATH.open(newline="", encoding="utf-8-sig") as input_file:
            reader = csv.DictReader(input_file)

            missing_columns = set(REQUIRED_FIELDS) - set(reader.fieldnames or [])
            if missing_columns:
                logger.error(
                    "Input file is missing required columns: %s",
                    ", ".join(sorted(missing_columns)),
                )
                return []

            for row_number, row in enumerate(reader, start=2):
                item = {
                    field: (row.get(field) or "").strip()
                    for field in REQUIRED_FIELDS
                }

                missing_values = [
                    field for field, value in item.items() if not value
                ]
                if missing_values:
                    logger.warning(
                        "skipping row %d: missing values for %s",
                        row_number,
                        ", ".join(missing_values),
                    )
                    continue

                request_id = item["request_id"]

                if request_id in seen_request_ids:
                    logger.warning(
                        "skipping duplicate request ID %s on row %d",
                        request_id,
                        row_number,
                    )
                    continue

                try:
                    claimed_amount = float(item["claimed_amount"])
                    if claimed_amount <= 0:
                        raise ValueError
                except ValueError:
                    logger.warning(
                        "skipping request %s: invalid claimed amount %r",
                        request_id,
                        item["claimed_amount"],
                    )
                    continue

                item["claimed_amount"] = claimed_amount
                seen_request_ids.add(request_id)
                items.append(item)

    except (OSError, csv.Error):
        logger.exception("could not read input file: %s", INPUT_PATH)
        return []

    logger.info("loaded %d valid reimbursement requests", len(items))
    return items


def web_interaction(item):
    """submit one reimbursement request through the local web protal ."""
    receipt=item.get("receipt")

    required_fields=("request_id","member_name","purpose","status")
    missing_fields=[
        field for field in required_fields if not item.get(field)
    ]
    if receipt is None:
        missing_fields.append("receipt")


    if missing_fields:
        logger.error(
            "cannot submit web form; missing data : %s",
            ", ".join(missing_fields)
        )
        return None


    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()

            try:
                page = browser.new_page()
                page.goto(
                    SITE_URL,
                    wait_until="domcontentloaded",
                    timeout=5000,

                )

                page.fill("#request-id", item["request_id"])
                page.fill("#member-name", item["member_name"])
                page.fill("#purpose", item["purpose"])
                page.fill("#vendor", receipt["vendor"])
                page.fill("#receipt-date", receipt["date"])
                page.fill("#amount", f"{receipt['amount_eur']:.2f}")
                page.select_option("#status", item["status"])


                page.click("#submit-request")
                confirmation = page.locator("#confirmation")
                confirmation.wait_for(state="visible", timeout=3000)

                message=confirmation.text_content().strip()
                logger.info("website confimaton: %s", message)
                return message
            finally:
                browser.close()



    except PlaywrightTimeoutError:
        logger.exception("Website timed out: %s", SITE_URL)
        return None
    except PlaywrightError:
        logger.exception("Playwright could not use website: %s", SITE_URL)
        return None


def parse_receipt_text(text):
    """Parse OCR text or return None when required information is unclear."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    date_match = DATE_PATTERN.search(text)
    total_marker = re.search(r"\bTOTAL\b", text, re.IGNORECASE)

    if date_match is None or total_marker is None:
        return None

    text_after_total = text[total_marker.end():]
    amounts = AMOUNT_PATTERN.findall(text_after_total)

    if not amounts:
        return None

    amount = float(amounts[-1].replace(",", "."))

    return {
        "vendor": lines[0],
        "date": date_match.group(0),
        "amount_eur": amount,
    }


def extract_from_document(image_path):
    """Run OCR on one receipt image and return parsed receipt data."""
    image_path = Path(image_path)

    if not image_path.is_absolute():
        image_path = BASE_DIR / image_path

    if not image_path.exists():
        logger.warning("Receipt file does not exist: %s", image_path)
        return None

    try:
        with Image.open(image_path) as image:
            text = pytesseract.image_to_string(image)
    except (OSError, UnidentifiedImageError, pytesseract.TesseractError):
        logger.exception("Could not OCR receipt: %s", image_path)
        return None

    receipt = parse_receipt_text(text)

    if receipt is None:
        logger.warning(
            "Could not confidently extract receipt data from %s",
            image_path.name,
        )
        return None

    logger.info(
        "Extracted receipt %s: %s, %s, %.2f EUR",
        image_path.name,
        receipt["vendor"],
        receipt["date"],
        receipt["amount_eur"],
    )
    return receipt


APPROVAL_THRESHOLD_EUR=50.00
def approval_status(amount_eur):
    """Return the decision used by the reimbursement portal."""
    if amount_eur <= APPROVAL_THRESHOLD_EUR:
        return "auto-approved"
    return "needs-president-approval"



def write_result(item, status, receipt=None, confirmation="", note=""):
    """Append one processing result to the CSV ledger."""
    receipt = receipt or {}

    row = {
        "request_id": item["request_id"],
        "member_name": item["member_name"],
        "purpose": item["purpose"],
        "claimed_amount": item["claimed_amount"],
        "receipt_vendor": receipt.get("vendor", ""),
        "receipt_date": receipt.get("date", ""),
        "receipt_amount": receipt.get("amount_eur", ""),
        "status": status,
        "confirmation": confirmation,
        "note": note,
    }

    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        new_file = not OUTPUT_PATH.exists()

        with OUTPUT_PATH.open("a", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=RESULT_FIELDS)

            if new_file:
                writer.writeheader()

            writer.writerow(row)
    except OSError:
        logger.exception("Could not write result for %s", item["request_id"])
        return False

    logger.info("Recorded result for request %s", item["request_id"])
    return True


def read_recorded_request_ids():
    """return request id's already present in the results ledger."""
    if not OUTPUT_PATH.exists():
        return set()

    try:
        with OUTPUT_PATH.open(newline="", encoding="utf-8") as output_file:
            reader = csv.DictReader(output_file)

            if not reader.fieldnames or "request_id" not in reader.fieldnames:
                logger.error("results file has no request_id column")
                return None

            return {
                row["request_id"]
                for row in reader
                if row.get("request_id")
            }
    except (OSError, csv.Error):
        logger.exception("could not read existing results: %s", OUTPUT_PATH)
        return None




def process_item(item):
    """Process one reimbursement request and return its final status."""
    request_id = item["request_id"]
    receipt = extract_from_document(item["receipt_file"])

    if receipt is None:
        status = "needs-review"
        note = "Receipt could not be read"

        logger.warning(
            "Request %s needs review because its receipt could not be processed",
            request_id,
        )

        if not write_result(item, status, note=note):
            return "output-error"

        return status

    amount_difference = abs(
        item["claimed_amount"] - receipt["amount_eur"]
    )

    if amount_difference > 0.01:
        status = "needs-review"
        note = (
            f"Claimed {item['claimed_amount']:.2f} EUR, "
            f"receipt shows {receipt['amount_eur']:.2f} EUR"
        )

        logger.warning("Request %s needs review: %s", request_id, note)

        if not write_result(item, status, receipt=receipt, note=note):
            return "output-error"

        return status

    status = approval_status(receipt["amount_eur"])

    web_item = item.copy()
    web_item["receipt"] = receipt
    web_item["status"] = status

    confirmation = web_interaction(web_item)

    if confirmation is None:
        status = "web-error"

        if not write_result(
            item,
            status,
            receipt=receipt,
            note="Website submission failed",
        ):
            return "output-error"

        return status

    if not write_result(
        item,
        status,
        receipt=receipt,
        confirmation=confirmation,
    ):
        return "output-error"

    logger.info("Completed request %s with status %s", request_id, status)
    return status

def main():
    items = read_input()
    recorded_ids=read_recorded_request_ids()


    if recorded_ids is None:
        logger.error("stopping because results file could not be read")
        return
    processed,needs_review, errored,skipped = 0, 0,0,0

    for item in items:
        request_id=item["request_id"]

        if request_id in recorded_ids:
            logger.info("skipping already recorded request %s",request_id)
            skipped += 1
            continue



        try:
            outcome=process_item(item)


        except Exception:

            logger.exception("Unexpected error processing %r", item)
            errored += 1
            continue

        if outcome in ("auto-approved", "needs-president-approval"):
            processed += 1
        elif outcome == "needs-review":
            needs_review += 1
        else:
            errored += 1

    logger.info("Done: %d processed, %d errored, %d needs review, %d skipped", processed, errored, needs_review, skipped)


if __name__ == "__main__":
    main()
