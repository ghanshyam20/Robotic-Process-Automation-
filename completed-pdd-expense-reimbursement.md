# Mini Process Definition Document (PDD)

Process name: Student club expense reimbursement
Author(s): Aarne Klemetti     Date: 26.8.2026

## 1. Process overview & goal

Goal: a club member who has paid for a club-related expense is reimbursed the correct amount to their bank account, with the expense recorded for the annual audit.

Actors: Requesting member (submits a receipt), Treasurer (processes requests, keeps records, initiates payment), Club president (approves reimbursements over €50).

## 2. As-Is steps

| # | Actor | Action |
|---|-------|--------|
| 1 | Member | Photographs a receipt and emails it to the treasurer with the amount, purpose, and budget category |
| 2 | Treasurer | Checks the email inbox for new requests (no fixed schedule) |
| 3 | Treasurer | Opens the receipt photo and checks it's readable (total, date, vendor visible) |
| 4 | Treasurer | Checks the amount against the €50 approval-threshold rule |
| 5 | Treasurer | (if over €50) Forwards the request to the club president and waits for a reply |
| 6 | President | Reviews the forwarded request and replies approving or rejecting it |
| 7 | Treasurer | Adds a row to the shared Excel ledger (date, member, amount, category, description) |
| 8 | Treasurer | Uploads the receipt photo to the Drive "Receipts" folder, named by date and member |
| 9 | Treasurer | Logs into the online banking portal and initiates a transfer to the member's IBAN on file |
| 10 | Treasurer | Replies to the original email thread confirming payment was sent |

## 3. Business rules & decision points

- Decision point: is the reimbursement amount over €50?
  - Rule: club reimbursement policy sets €50 as the treasurer's sole-approval limit
  - Path A (≤ €50): treasurer approves directly, proceeds to ledger entry (step 7)
  - Path B (> €50): treasurer forwards to the president (step 5); process only continues once the president replies — if rejected, the process ends and the member should be notified (not explicitly stated in the narrative, but implied — worth flagging as a gap to confirm with the SME in a real PDD)

## 4. Exceptions

**Business exceptions**

- Amount exceeds €50: routes to president approval instead of treasurer-only approval (see
  Section 3 — this is a valid, expected path, not a failure)
- President rejects the request: process ends without payment (narrative doesn't state what happens next — flag as an open question for the SME)

**Application exceptions**

- Receipt photo is unreadable (blurry, cropped, ~1 in 8 requests): treasurer cannot proceed;
  requests a new photo from the member by email; the request sits unprocessed until a usable photo arrives — no timeout or escalation described
- Bank transfer rejected due to an out-of-date IBAN: treasurer emails the member for current bank details and retries the transfer once received — the ledger entry and receipt filing (steps 7–8) have already happened by this point, so the record exists even though payment
  hasn't gone out yet

## 5. In scope / out of scope for RPA

In scope (bot could plausibly do this, as described):
- Checking the inbox for new requests
- Basic receipt-photo quality checks and OCR extraction of amount/date/vendor (Session 7/10
  territory — not achievable with rule-based logic alone, since "readable" is a judgment call today; this is exactly the kind of step that motivates this course's AI-augmented sessions)
- Applying the €50 threshold rule and routing accordingly
- Writing the ledger row and filing the receipt photo
- Initiating the bank transfer, given a validated IBAN

Out of scope (needs human judgment, or is a hard gate):
- The president's actual approval decision for >€50 requests — this is a human judgment call by design, not something to automate
- Deciding what counts as an acceptable expense in the first place (budget-category judgment calls) — not described as automatable in the narrative and not something the process owner asked to change here

## 6. Volumes, frequency & systems touched

- Volume: 15–20 requests/month on average, with spikes in October–November (competition season)
- Frequency: on-demand as requests arrive; treasurer currently batches processing a few times a week rather than continuously
- Systems touched: email inbox, receipt photos (unstructured images), shared Excel ledger on Google Drive, Drive "Receipts" folder, online banking portal, separate member-IBAN spreadsheet
