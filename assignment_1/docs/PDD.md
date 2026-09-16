# Mini Process Definition Document (PDD)

Process name: Student club expense reimbursement

Author(s): Ghan Shyam Bhattarai     Date: 26.08.2026

Document the process **as it happens today (As-Is)** — not how you'd redesign it for a bot. That design step comes later, once the process is understood.

## 1. Process overview & goal

* What is this process for? What's the end goal when it completes successfully?
* Who are the actors involved (roles, not names)?

```text
Goal:
The goal is to reimburse a club member for an approved club-related expense and keep a record for the annual audit.

Actors:
- Club member
- Treasurer
- Club president
- Bank
```

## 2. As-Is steps

Number each step. One actor and one action per step.

| #  | Actor          | Action                                                                |
| -- | -------------- | --------------------------------------------------------------------- |
| 1  | Club member    | Takes a photo of the paper receipt.                                   |
| 2  | Club member    | Emails the receipt photo to the treasurer.                            |
| 3  | Club member    | Includes the purpose and budget category in the email.                |
| 4  | Treasurer      | Checks the reimbursement email inbox a few times per week.            |
| 5  | Treasurer      | Opens a reimbursement request email.                                  |
| 6  | Treasurer      | Checks whether the receipt photo is readable.                         |
| 7  | Treasurer      | Checks the reimbursement amount.                                      |
| 8  | Treasurer      | Approves a reimbursement of €50 or less.                              |
| 9  | Treasurer      | Forwards a reimbursement over €50 to the club president.              |
| 10 | Club president | Reviews the forwarded reimbursement request.                          |
| 11 | Club president | Sends an approval or rejection to the treasurer.                      |
| 12 | Treasurer      | Adds the approved expense details to the shared Excel expense ledger. |
| 13 | Treasurer      | Uploads the receipt photo to the Google Drive Receipts folder.        |
| 14 | Treasurer      | Looks up the member's IBAN in the separate IBAN spreadsheet.          |
| 15 | Treasurer      | Initiates a bank transfer for the approved amount.                    |
| 16 | Bank           | Processes the transfer.                                               |
| 17 | Treasurer      | Emails the member that payment has been sent.                         |

## 3. Business rules & decision points

For each point where the process branches, state the rule and both paths.

* Decision point: Is the receipt photo readable?

  * Rule: The total amount, date, and vendor name must be visible.
  * Path A: If the receipt is readable, the treasurer checks the reimbursement amount.
  * Path B: If the receipt is unreadable, the treasurer asks the member for a clearer photo and waits.

* Decision point: Is the reimbursement amount €50 or less?

  * Rule: Reimbursements up to and including €50 can be approved by the treasurer. Amounts over €50 need approval from the club president.
  * Path A: If the amount is €50 or less, the treasurer approves it and continues with recording the expense.
  * Path B: If the amount is over €50, the treasurer forwards it to the president and waits for approval or rejection. If approved, the treasurer records the expense. If rejected, the member is not reimbursed.

* Decision point: Does the bank transfer succeed?

  * Rule: The transfer needs a valid and current IBAN.
  * Path A: If successful, the treasurer emails the member that payment has been sent.
  * Path B: If rejected, the treasurer asks the member for their current IBAN and tries the transfer again.

## 4. Exceptions

**Business exceptions** — valid-but-different paths through the real process.

```text
A reimbursement over €50 needs approval from the club president before the treasurer can continue.

The club president may reject a reimbursement request. In that case, the member is not reimbursed.
```

**Application exceptions** — something breaking and the real fallback used today.

```text
If the receipt photo is blurry or cut off, the treasurer cannot read the total amount, date, or vendor name. The treasurer emails the member asking for a clearer receipt photo and waits.

If the bank rejects the transfer because the stored IBAN is outdated, the treasurer emails the member asking for their current IBAN before trying the transfer again.
```

## 5. In scope / out of scope for RPA

* In scope (a bot could plausibly do this step, as described):

```text
Checking the email inbox for reimbursement requests.
Reading standard details from emails.
Adding approved expense details to the Excel ledger.
Uploading receipt files to the Google Drive Receipts folder.
Looking up the member's IBAN in the IBAN spreadsheet.
Sending payment confirmation emails.
```

* Out of scope (requires human judgment, or isn't a good candidate — say why):

```text
Checking whether a receipt photo is readable, because it needs human judgment.
Approving reimbursements over €50, because the president's approval is required.
Making the final bank transfer, because it involves financial authorization and security.
Deciding whether an expense is club-related, because this may need human judgment.
```

## 6. Volumes, frequency & systems touched

* Volume: how many instances of this process run, per what time period?
* Frequency: how often does it need to run?
* Systems touched: list every system/application a human interacts with to complete this process.

```text
Volume: Around 15–20 reimbursement requests per month. The volume is higher during competition season, especially in October and November.

Frequency: The treasurer checks the email inbox a few times per week. There is no fixed schedule.

Systems touched:
- Email inbox
- Receipt photos
- Shared Excel expense ledger
- Google Drive
- Google Drive Receipts folder
- Online banking portal
- Separate spreadsheet containing members' IBANs
```
