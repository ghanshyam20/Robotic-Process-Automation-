# Student Club Expense Reimbursement Bot

This project is a classical/hybrid RPA bot for processing student club
reimbursement requests.

The bot reads requests from a CSV work queue, extracts information from receipt
images with OCR, applies the club's approval rule, and submits valid requests
through a local reimbursement website using Playwright. It records every result
in a CSV ledger and writes execution details to a log file.


## Bot process flow

The following diagram shows the main processing flow of the bot.

![Bot process flow](docs/bot_process_flow.drawio)

## Process rule

- Expenses of €50.00 or less are auto-approved.
- Expenses over €50.00 require approval from the club president.
- An unreadable or missing receipt is sent for manual review.
- A claimed amount that differs from the receipt amount is sent for manual
  review.
- The bot does not make bank transfers.

## Main features

- Reads and validates reimbursement requests from `requests.csv`.
- Skips incomplete, duplicated, or invalid input rows.
- Uses Tesseract OCR to extract the vendor, date, and total from receipt images.
- Uses Playwright to fill and submit the reimbursement web form.
- Handles missing files, unreadable receipts, Playwright failures, and invalid
  input without stopping the complete batch.
- Writes progress and errors to `bot.log`.
- Writes outcomes to `output/results.csv`.
- Skips requests already present in the results ledger.

## Project structure

```text
assignment_1/
├── bot.py
├── requests.csv
├── requirements.txt
├── receipts/
│   ├── receipt_001.png
│   ├── receipt_002.png
│   └── receipt_003.png
├── site/
│   └── reimbursement.html
├── output/
├── docs/
│   ├── PDD.md
│   └── WRITEUP.md
└── README.md



```

## Requirements

- Python 3
- Tesseract OCR
- Playwright with Chromium
- Python packages listed in `requirements.txt`

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Install the Playwright browser if it is not already installed:

```bash
playwright install chromium
```

Tesseract must also be installed on the computer and available from the command line.

## Running the bot

From the `assignment_1` directory, run:

```bash
python bot.py
```

The bot creates:

- `bot.log` containing processing and error messages
- `output/results.csv` containing one result per valid request

## Sample cases

The included work queue demonstrates several paths:

- `REQ001`: valid receipt and auto-approved
- `REQ002`: valid receipt and requires president approval
- `REQ003`: deliberately difficult receipt and routed to manual review
- `REQ004`: missing receipt and routed to manual review
- `REQ005`: invalid claimed amount and rejected during input validation

Running the bot a second time does not create duplicate result rows. Requests already found in `output/results.csv` are skipped.

To perform a new demonstration from an empty results ledger, remove only the generated file:

```bash
rm output/results.csv
python bot.py
```

## Known limitations

- OCR parsing expects a date in `YYYY-MM-DD` format and an identifiable `TOTAL`.
- Poor image quality may cause a receipt to require manual review.
- The included reimbursement portal is a local demonstration website.
- The bot records approval decisions but does not perform payments or send emails.