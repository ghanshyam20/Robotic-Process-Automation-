# Assignment 1 – Short Write-up

## Student Club Expense Reimbursement Bot

For this assignment, I developed a bot that processes expense reimbursement requests for a student club. The idea came from the manual reimbursement process described in my Process Definition Document. The purpose of the bot is to reduce the repetitive work done by the treasurer while keeping uncertain cases for manual review.

The bot starts by reading reimbursement requests from a CSV file. It checks that the required fields exist, validates the claimed amount, and ignores invalid or duplicate requests. Each valid request contains details such as the request ID, member name, purpose, claimed amount, and receipt file.

After reading a request, the bot uses Tesseract OCR to extract the vendor name, receipt date, and total amount from the receipt image. I decided that the bot should not guess when the OCR result is unclear. If the receipt is missing or the required information cannot be extracted, the request is recorded as `needs-review`. The bot also compares the amount claimed in the CSV file with the amount found on the receipt. If the amounts do not match, the request is sent for manual review.

The approval decision follows the rule from my PDD. An amount of €50.00 or less is marked as `auto-approved`. An amount above €50.00 is marked as `needs-president-approval`.

For the website interaction, I created a small local reimbursement portal and automated it using Playwright. The bot opens the page, fills in the request and receipt details, selects the correct decision, submits the form, and reads the confirmation message. Using a local website makes the demonstration repeatable and avoids depending on an external service.

The bot writes its progress and errors to `bot.log`. It also records the result of each request in `output/results.csv`. Before processing, it reads the existing result IDs and skips requests that were already recorded. This prevents duplicate submissions when the bot is run more than once.

I tested the bot with different sample cases. One request is auto-approved, one requires president approval, one has a difficult receipt that OCR cannot read confidently, one has a missing receipt, and one has an invalid claimed amount. These cases confirmed that one bad request does not stop the whole batch.

The main limitations are that the OCR parser expects a date in `YYYY-MM-DD` format and looks for a recognizable `TOTAL`. Receipt layouts with different formats may need additional parsing rules. The website is a local demonstration, and the bot does not make payments, send emails, or replace the president’s approval. Those actions remain outside the scope because they involve authorization, security, or human judgment.
