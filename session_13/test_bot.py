"""Given — a complete set of pytest examples against reimbursement_bot.py
(Session 8's bot, unchanged). Nothing to fill in here; read it for the
patterns (fixtures, tmp_path, parametrize) before writing monitor.py's TODO.
Run: pytest test_bot.py -v
"""
import pytest
from RPA.Tables import Tables

from reimbursement_bot import approval_status, read_request


@pytest.fixture
def tables():
    return Tables()


@pytest.mark.parametrize("amount_eur,expected", [
    (25.00, "auto-approved"),
    (50.00, "auto-approved"),
    (50.01, "needs manager approval"),
    (200.00, "needs manager approval"),
])
def test_approval_status(amount_eur, expected):
    assert approval_status(amount_eur) == expected


def test_read_request_valid(tmp_path, tables):
    csv_path = tmp_path / "request_001.csv"
    csv_path.write_text(
        "request_id,member_name,amount_eur,category,date,description\n"
        "R001,Aino Korhonen,17.40,Consumables,2026-09-03,Solder wire\n"
    )

    request = read_request(csv_path, tables)

    assert request is not None
    assert request["member_name"] == "Aino Korhonen"
    assert request["amount_eur"] == 17.40
    assert isinstance(request["amount_eur"], float)


def test_read_request_missing_field_returns_none(tmp_path, tables):
    csv_path = tmp_path / "request_002.csv"
    csv_path.write_text(
        "request_id,member_name,amount_eur,category,date,description\n"
        "R002,Miika Salo,,Events,2026-09-04,Competition entry fee\n"
    )

    assert read_request(csv_path, tables) is None


def test_read_request_non_numeric_amount_returns_none(tmp_path, tables):
    csv_path = tmp_path / "request_003.csv"
    csv_path.write_text(
        "request_id,member_name,amount_eur,category,date,description\n"
        "R003,Elina Virtanen,not-a-number,Admin,2026-09-05,Printing\n"
    )

    assert read_request(csv_path, tables) is None
