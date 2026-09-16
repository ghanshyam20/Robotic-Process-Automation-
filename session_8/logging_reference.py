"""Reference example: logging and exception handling for RPA bots.

This is a standalone teaching artifact, not an exercise — read it, run it, then
apply the same patterns to retrofit_reimbursement_bot.py. Run: python logging_reference.py
"""
import logging
from pathlib import Path

LOG_PATH = Path(__file__).parent / "reference.log"

# A named logger (not the root logger) so multiple modules in a larger project
# don't fight over configuration. Two handlers: console gets INFO and up, kept
# short; the file gets everything (DEBUG and up) with full detail, for later
# review — this is the standard "human sees a summary, the file has the record"
# split.
logger = logging.getLogger("reference")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

file_handler = logging.FileHandler(LOG_PATH, mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class UnrecoverableBotError(Exception):
    """Raised when the bot can't reasonably continue at all (not per-item)."""


def process_item(value):
    """Doubles a number. Deliberately fragile, to demonstrate two kinds of failure."""
    logger.debug("Processing item: %r", value)

    if not isinstance(value, (int, float)):
        # Expected, recoverable: this specific item is bad, but the batch can continue.
        logger.warning("Skipping non-numeric item %r", value)
        return None

    return value * 2


def load_batch(source):
    """Simulates a setup step that must succeed before any items can be processed."""
    if source is None:
        # Not recoverable: there's nothing to process without a valid source.
        # Log the full traceback context, then raise a clear, typed error rather
        # than letting a bare ValueError/TypeError propagate with no context.
        try:
            raise ValueError("batch source was None")
        except ValueError as exc:
            logger.exception("Could not load batch")
            raise UnrecoverableBotError("no batch source provided") from exc
    return source


def main():
    batch = load_batch([1, 2, "not a number", 4, None, 5])

    results = []
    errors = 0
    for item in batch:
        try:
            result = process_item(item)
        except Exception:
            # Broad on purpose: this is the "something unexpected happened with
            # this one item" catch. Log the full traceback (logger.exception
            # only makes sense inside an except block — it captures sys.exc_info()
            # automatically) and keep going rather than crashing the whole batch.
            logger.exception("Unexpected error processing item %r", item)
            errors += 1
            continue

        if result is not None:
            results.append(result)

    logger.info("Done: %d results, %d errors", len(results), errors)
    return results


if __name__ == "__main__":
    main()
