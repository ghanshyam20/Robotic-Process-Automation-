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


def process_item(item):
    """TODO: tie the above together for one item.

    Wrap risky per-item steps in try/except — an unexpected failure on one item
    should be logged (logger.exception(...)) and shouldn't crash the whole batch
    (Session 8's pattern). Return whatever outcome/status this item ended with,
    or raise if the item should be flagged for review.
    """
    raise NotImplementedError


def main():
    items = read_input()
    processed, errored = 0, 0

    for item in items:
        try:
            process_item(item)
            processed += 1
        except Exception:
            # Broad on purpose — the "something unexpected happened with this one
            # item" catch. Narrow, expected failures (e.g. OCR couldn't read a
            # receipt) should be handled inside process_item itself, not here.
            logger.exception("Unexpected error processing %r", item)
            errored += 1

    logger.info("Done: %d processed, %d errored", processed, errored)


if __name__ == "__main__":
    main()
