"""Session 13 exercise: a monitoring/alerting pass over a bot's log file.

Fill in the one TODO function: `find_alerts`. Everything else (reporting,
writing to alerts.log, the CLI) is given.

Unlike every earlier exercise, there's no check_solution.py here — this
session's checker IS pytest. Once find_alerts is implemented, run:

    pytest -v

test_monitor.py (given, not yours to edit) drives find_alerts directly with
crafted log content — no need to run reimbursement_bot.py first just to test
your logic. test_bot.py (also given) is a second, complete set of pytest
examples against reimbursement_bot.py itself — read it for the patterns
(fixtures, tmp_path, parametrize) even though there's nothing to fill in there.
"""
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
LOG_PATH = BASE_DIR / "bot.log"
ALERTS_LOG_PATH = BASE_DIR / "alerts.log"

ALERT_LEVELS = {"ERROR", "CRITICAL"}
LEVEL_PATTERN = re.compile(r"\b(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b")


def find_alerts(log_path):
    """TODO: return a list of (level, line) tuples for every log line at
    ERROR level or above.

    A log line's level is the first DEBUG/INFO/WARNING/ERROR/CRITICAL word
    found in it (matches this course's logging format from Session 8:
    "TIMESTAMP LEVEL NAME: MESSAGE"). WARNING is informational, not
    alert-worthy — only ERROR and CRITICAL count.

    1. Read `log_path` and split it into lines (`Path(log_path).read_text().splitlines()`).
    2. For each line, search for a level using `LEVEL_PATTERN.search(line)`
       (already defined above — matches this file's own imports, don't rewrite it).
    3. If there's a match and the matched level is in ALERT_LEVELS, append
       `(level, line)` to your results.
    4. Return the list.

    Watch out for traceback lines: a Python traceback following an ERROR log
    line has no level keyword of its own (it's just "File ..., line 105, in
    main"), so it correctly won't match — each *logged* error becomes exactly
    one alert, not one per traceback line. test_monitor.py checks this directly.
    """
    alerts = []

    lines = Path(log_path).read_text().splitlines()

    for line in lines:
        match = LEVEL_PATTERN.search(line)

        if match:
            level = match.group(1)

            if level in ALERT_LEVELS:
                alerts.append((level, line))

    return alerts


def report(alerts):
    if not alerts:
        print("All clear — no errors in the last run.")
        return

    print(f"ALERT: {len(alerts)} issue(s) found in the last run:")
    for level, line in alerts:
        print(f"  [{level}] {line}")

    with open(ALERTS_LOG_PATH, "a") as f:
        f.write(f"--- {datetime.now().isoformat()} — {len(alerts)} alert(s) ---\n")
        for level, line in alerts:
            f.write(f"{line}\n")


def main():
    if not LOG_PATH.exists():
        print(f"No log file found at {LOG_PATH} — run reimbursement_bot.py first.")
        return
    alerts = find_alerts(LOG_PATH)
    report(alerts)


if __name__ == "__main__":
    main()
