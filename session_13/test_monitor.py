"""Given — this is what "done" looks like for monitor.py's find_alerts TODO.
Don't edit this file; make find_alerts satisfy it. Run: pytest test_monitor.py -v
"""
from monitor import find_alerts

SAMPLE_LOG = """\
2026-08-18 20:10:58,100 DEBUG reimbursement_bot: Processing request_001.csv
2026-08-18 20:10:58,101 INFO reimbursement_bot: request_001.csv: auto-approved (25.50 EUR)
2026-08-18 20:10:58,102 WARNING reimbursement_bot: request_005.csv: missing required field 'amount_eur'
2026-08-18 20:10:58,188 ERROR reimbursement_bot: Unexpected error reading request_007.csv
Traceback (most recent call last):
  File "reimbursement_bot.py", line 105, in main
_csv.Error: Could not determine delimiter
2026-08-18 20:10:58,200 INFO reimbursement_bot: Processed: 1, needs manager approval: 0
"""


def test_finds_error_lines(tmp_path):
    log_path = tmp_path / "bot.log"
    log_path.write_text(SAMPLE_LOG)

    alerts = find_alerts(log_path)

    assert len(alerts) == 1
    level, line = alerts[0]
    assert level == "ERROR"
    assert "request_007.csv" in line


def test_warning_is_not_an_alert(tmp_path):
    log_path = tmp_path / "bot.log"
    log_path.write_text(SAMPLE_LOG)

    alerts = find_alerts(log_path)

    assert not any("request_005.csv" in line for _level, line in alerts)


def test_traceback_lines_dont_produce_extra_alerts(tmp_path):
    log_path = tmp_path / "bot.log"
    log_path.write_text(SAMPLE_LOG)

    alerts = find_alerts(log_path)

    # The traceback under the ERROR line has no level keyword of its own —
    # it shouldn't be counted as a second, separate alert.
    assert len(alerts) == 1


def test_clean_log_has_no_alerts(tmp_path):
    log_path = tmp_path / "bot.log"
    log_path.write_text(
        "2026-08-18 20:10:58,100 INFO reimbursement_bot: request_001.csv: auto-approved\n"
        "2026-08-18 20:10:58,200 INFO reimbursement_bot: Processed: 1, needs manager approval: 0\n"
    )

    assert find_alerts(log_path) == []
