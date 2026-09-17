"""Session 9 exercise: classify expense requests with a local LLM.

Fill in the one TODO function: `classify_description`. Everything else (reading
requests, the report, comparing against the self-reported category, moving
files) is given. Run: python classify_requests.py
Check your work: python check_solution.py

Each request already has a member-supplied `category` (Equipment/Events/Admin/
Consumables) — the same field from Session 3/4's PDD. Today's bot independently
classifies the request from its free-text `description` using Ollama, and flags
any disagreement for a human to check. Members do sometimes miscategorize their
own requests — that's not a bug in the data, it's the reason this bot is useful.
"""
import logging
from pathlib import Path

import ollama
from RPA.Excel.Files import Files
from RPA.FileSystem import FileSystem
from RPA.Tables import Tables

MODEL = "llama3.1:8b"
CATEGORIES = ["Equipment", "Events", "Admin", "Consumables"]
SYSTEM_PROMPT = """You classify club expense descriptions into exactly one budget category.
Categories:
- Equipment: tools, parts, hardware, components
- Events: competition fees, travel, catering for club events
- Admin: printing, office supplies, administrative costs
- Consumables: solder, glue, tape, and other one-time-use materials

Reply with ONLY the category name, nothing else."""

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
PROCESSED_DIR = BASE_DIR / "processed"
NEEDS_REVIEW_DIR = BASE_DIR / "needs_review"
REPORT_PATH = BASE_DIR / "classification_report.xlsx"
LOG_PATH = BASE_DIR / "bot.log"

REQUIRED_FIELDS = ["request_id", "member_name", "description", "category"]
REPORT_HEADERS = ["request_id", "member_name", "description", "reported_category", "llm_category", "result"]

logger = logging.getLogger("classify_requests")
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

    return row


def classify_description(description):
    """TODO: ask the local LLM to classify `description`, and return one of
    CATEGORIES — or None if the model's answer isn't usable.

    1. Call `ollama.chat(model=MODEL, options={"temperature": 0}, messages=[...])`
       with two messages: a "system" message using SYSTEM_PROMPT (defines the
       categories), and a "user" message containing `description`.
       `temperature: 0` makes the model's answer as deterministic as possible —
       useful here since you want the same input to reliably classify the same
       way.
    2. The model's reply text is at `response["message"]["content"]` — strip it.
    3. Check the stripped text is exactly one of CATEGORIES. If it's not (the
       model can and sometimes does return something else — extra words, a
       category not in your list, or worse), log a warning and return None.
       This is the same "don't trust unstructured output blindly" idea from
       Session 7's OCR parsing — a local LLM's text output needs the same
       defensive validation before you act on it.
    4. Otherwise return the predicted category.
    """
    response=ollama.chat(
        model=MODEL,
        options={"temperature": 0},
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":description}
        ],
    )
    category=response["message"]["content"].strip()

    if category not in CATEGORIES:
        logger.warning("LLM returned an unexpected category: %r", category)
        return None
    return category


def ensure_report(excel):
    try:
        if REPORT_PATH.exists():
            excel.open_workbook(str(REPORT_PATH))
        else:
            excel.create_workbook(path=str(REPORT_PATH), sheet_name="Classification")
            excel.append_rows_to_worksheet([REPORT_HEADERS])
            excel.save_workbook()
    except Exception:
        logger.exception("Could not open or create the report workbook — cannot continue")
        raise


def append_to_report(excel, request, llm_category, result):
    row = [request["request_id"], request["member_name"], request["description"],
           request["category"], llm_category, result]
    excel.append_rows_to_worksheet([row])


def main():
    fs = FileSystem()
    tables = Tables()
    excel = Files()

    fs.create_directory(str(PROCESSED_DIR), exist_ok=True)
    fs.create_directory(str(NEEDS_REVIEW_DIR), exist_ok=True)
    ensure_report(excel)

    csv_files = sorted(INPUT_DIR.glob("*.csv"))
    matched, mismatched, skipped, flagged = 0, 0, 0, 0

    for csv_path in csv_files:
        logger.debug("Processing %s", csv_path.name)

        request = read_request(csv_path, tables)
        if request is None:
            skipped += 1
            continue

        llm_category = classify_description(request["description"])

        if llm_category is None:
            logger.warning("%s: could not get a usable classification — needs review", csv_path.name)
            fs.move_file(str(csv_path), str(NEEDS_REVIEW_DIR / csv_path.name), overwrite=True)
            flagged += 1
            continue

        if llm_category == request["category"]:
            result = "match"
            matched += 1
        else:
            result = "mismatch"
            mismatched += 1
            logger.warning("%s: reported %r but LLM says %r", csv_path.name,
                            request["category"], llm_category)

        append_to_report(excel, request, llm_category, result)
        logger.info("%s: %s (reported=%s, llm=%s)", csv_path.name, result,
                    request["category"], llm_category)
        fs.move_file(str(csv_path), str(PROCESSED_DIR / csv_path.name), overwrite=True)

    excel.save_workbook()
    excel.close_workbook()

    logger.info(
        "Matched: %d, mismatched: %d, needs review: %d, skipped (invalid): %d",
        matched, mismatched, flagged, skipped,
    )


if __name__ == "__main__":
    main()
