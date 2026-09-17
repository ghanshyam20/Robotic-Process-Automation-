"""Session 10 exercise: hybrid OCR+LLM document extractor.

Fill in the two TODO functions: `llm_extract` and the fallback logic inside
`extract_receipt`. `regex_extract` (Session 7, unchanged) and everything else
(the ledger, logging, moving files) is given. Run: python hybrid_extract.py
Check your work: python check_solution.py

This is the same receipts/ folder from Session 7 — including receipt_003.png,
the one whose garbled OCR text defeated regex extraction back then. Today you
add a second extraction method that can succeed where regex can't, and combine
the two: cheap and deterministic first, LLM as a fallback, always flagged for
review when the fallback is used.
"""
import json
import logging
import re
from pathlib import Path

import ollama
import pytesseract
from PIL import Image
from RPA.Excel.Files import Files
from RPA.FileSystem import FileSystem

MODEL = "llama3.1:8b"
BASE_DIR = Path(__file__).parent
RECEIPTS_DIR = BASE_DIR / "receipts"
PROCESSED_DIR = BASE_DIR / "processed"
NEEDS_REVIEW_DIR = BASE_DIR / "needs_review"
LEDGER_PATH = BASE_DIR / "extraction_report.xlsx"
LOG_PATH = BASE_DIR / "bot.log"

LEDGER_HEADERS = ["source_file", "vendor", "date", "amount_eur", "extraction_method", "needs_review"]
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
TOTAL_PATTERN = re.compile(r"TOTAL.*?(\d+\.\d{2})", re.IGNORECASE)

LLM_SYSTEM_PROMPT = """You extract structured data from noisy OCR text of a receipt. The OCR
software makes mistakes (misread characters, garbled words) — use context to recover the
likely intended values. Respond with ONLY a JSON object with exactly these keys:
vendor (string), date (string, YYYY-MM-DD), total_eur (number).
If you cannot confidently determine a field, use null for that field."""

logger = logging.getLogger("hybrid_extract")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

file_handler = logging.FileHandler(LOG_PATH, mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def regex_extract(text):
    """Given — Session 7's extraction, unchanged."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    vendor = lines[0]

    date_match = DATE_PATTERN.search(text)
    if not date_match:
        return None
    date = date_match.group(0)

    total_match = TOTAL_PATTERN.search(text)
    if not total_match:
        return None
    amount_eur = float(total_match.group(1))

    return {"vendor": vendor, "date": date, "amount_eur": amount_eur}


def llm_extract(text):
    """TODO: ask the local LLM to extract vendor/date/amount from `text` as JSON.

    1. Call `ollama.chat(model=MODEL, options={"temperature": 0}, format="json",
       messages=[...])` with a "system" message (LLM_SYSTEM_PROMPT) and a "user"
       message containing `text`. `format="json"` tells Ollama to constrain the
       model's output to valid JSON — still worth validating, not a guarantee the
       *content* is right, only that it parses.
    2. Parse `response["message"]["content"]` with `json.loads(...)`, inside a
       try/except catching `json.JSONDecodeError` — return None if parsing fails.
    3. Pull out "vendor", "date", "total_eur" from the parsed dict with `.get(...)`.
       If any of them is missing/falsy (the model used `null`, meaning it wasn't
       confident), return None — same "don't guess" idea as Session 7 and 9.
    4. Otherwise return {"vendor": ..., "date": ..., "amount_eur": float(...)}.
    """
    response = ollama.chat(
        model=MODEL,
        options={"temperature": 0},
        format="json",
        messages=[
            {"role": "system", "content": LLM_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )

    try:
        data=json.loads(response["message"]["content"])
    except json.JSONDecodeError:
        logger.warning("LLM returned invalid JSON: %s", response["message"]["content"])
        return None

    vendor = data.get("vendor")
    date = data.get("date")
    total_eur = data.get("total_eur")

    if not vendor or not date or not total_eur:
        return None

    return{
        "vendor": vendor,
        "date": date,
        "amount_eur": float(total_eur)
    }



def extract_receipt(image_path):
    """TODO: try regex_extract first; only call llm_extract if that fails.

    1. OCR the image: `text = pytesseract.image_to_string(Image.open(image_path))`.
    2. Call `regex_extract(text)`. If it returns a result (not None), return
       `(result, "regex", False)` — regex succeeded, no review needed.
    3. Otherwise, log (logger.info) that regex failed and you're falling back to
       the LLM, then call `llm_extract(text)`.
       - If it returns a result, return `(result, "llm", True)` — always flagged
         for review when the LLM fallback is used, regardless of what the model
         seems confident about. (Worth testing yourself: ask the model to also
         report its own confidence, and see whether that confidence is actually
         trustworthy on this receipt. It isn't — see exercise-solution notes if
         you want to compare after you've tried it.)
       - If llm_extract also returns None, return `(None, None, True)` —
         extraction failed entirely.
    """
    text= pytesseract.image_to_string(Image.open(image_path),config="--psm 6")
    result=regex_extract(text)
    if result is not None:
        return (result, "regex", False)

    logger.info("Regex extraction failed -falling back to LLM")

    llm_result=llm_extract(text)

    if llm_result is not None:
        return (llm_result, "llm", True)
    return (None, None, True)


def ensure_ledger(excel):
    try:
        if LEDGER_PATH.exists():
            excel.open_workbook(str(LEDGER_PATH))
        else:
            excel.create_workbook(path=str(LEDGER_PATH), sheet_name="Extraction")
            excel.append_rows_to_worksheet([LEDGER_HEADERS])
            excel.save_workbook()
    except Exception:
        logger.exception("Could not open or create the report workbook — cannot continue")
        raise


def main():
    fs = FileSystem()
    excel = Files()

    fs.create_directory(str(PROCESSED_DIR), exist_ok=True)
    fs.create_directory(str(NEEDS_REVIEW_DIR), exist_ok=True)
    ensure_ledger(excel)

    image_paths = sorted(RECEIPTS_DIR.glob("*.png"))
    regex_count, llm_count, failed = 0, 0, 0

    for image_path in image_paths:
        logger.debug("Processing %s", image_path.name)
        result, method, needs_review = extract_receipt(image_path)

        if result is None:
            logger.warning("%s: extraction failed entirely (regex and LLM) — needs review",
                            image_path.name)
            fs.move_file(str(image_path), str(NEEDS_REVIEW_DIR / image_path.name), overwrite=True)
            failed += 1
            continue

        row = [image_path.name, result["vendor"], result["date"], result["amount_eur"],
               method, needs_review]
        excel.append_rows_to_worksheet([row])

        if method == "regex":
            logger.info("%s: extracted via regex — %s / %s / %.2f EUR",
                        image_path.name, result["vendor"], result["date"], result["amount_eur"])
            regex_count += 1
            fs.move_file(str(image_path), str(PROCESSED_DIR / image_path.name), overwrite=True)
        else:
            logger.info("%s: extracted via LLM fallback (needs review) — %s / %s / %.2f EUR",
                        image_path.name, result["vendor"], result["date"], result["amount_eur"])
            llm_count += 1
            fs.move_file(str(image_path), str(NEEDS_REVIEW_DIR / image_path.name), overwrite=True)

    excel.save_workbook()
    excel.close_workbook()

    logger.info(
        "Extracted via regex: %d, via LLM fallback: %d, failed entirely: %d",
        regex_count, llm_count, failed,
    )


if __name__ == "__main__":
    main()
