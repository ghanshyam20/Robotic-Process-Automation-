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
import logging
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_PATH = BASE_DIR / "bot.log"

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
    """TODO: read your input file(s) — CSV, Excel, or a generated work queue.

    Use RPA.Tables, RPA.Excel.Files, RPA.FileSystem, or plain Python — whichever
    fits your process. Return an iterable of items to process (dicts are a
    reasonable default, matching the pattern from Sessions 4/7).
    """
    raise NotImplementedError


def web_interaction(item):
    """TODO: interact with a website using Playwright for this item.

    Needs at least one real interaction beyond just loading a page — filling a
    form, clicking something, selecting an option, or extracting data via a
    locator (Session 5's pattern). Return whatever your process needs from it.
    """
    raise NotImplementedError


def extract_from_document(image_path):
    """TODO: OCR a scanned/image-based document with pytesseract, and parse the
    result defensively.

    Follow Session 7's pattern: return None (don't guess) if you can't confidently
    extract what you need, so the caller can route it for review instead of
    silently logging something wrong.
    """
    raise NotImplementedError


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
