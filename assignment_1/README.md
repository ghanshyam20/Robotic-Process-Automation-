# Assignment 1 starter code

## Learning objective

A starting structure for Assignment 1 — see `../spec.md` for the full requirements and
`../rubric.md` for how it's graded. This is not tied to any specific process; adapt it to
whatever process you scoped in your Session 3 PDD.

## Prerequisites

- Your own Session 3 mini-PDD (or a new one, for whatever process you're automating) — you should
  know your process's steps, business rules, and exceptions before writing code against it
- Everything from Sessions 4–8: `rpaframework` (files/Excel), Playwright, OCR (`pytesseract`),
  logging and exception handling — this assignment combines all of them

## Setup steps

Use the same virtual environment from Session 2 — no new installs needed, everything required
(`rpaframework`, `playwright`, `pytesseract`, standard library `logging`) is already there.

Copy `bot.py` as your starting point. Its four TODO functions map directly to the spec's four
technical requirements (file input, web interaction, OCR extraction, error handling — logging is
already wired up for you). You don't have to keep this exact structure — split it into more
files, rename things, reorder the pipeline — but by the end your submission needs to cover the
same four things.

You'll need your own input data and target website for your chosen process — these aren't
provided, since your process is your own. If your process doesn't naturally have a web-automation
or OCR step, look back at your PDD: is there a system-lookup step that could become the web
interaction, or a scanned/photographed document you could OCR? Most real processes have more
candidate steps than the ones you first think of.

## How to verify success

There's no automated checker here (unlike the session exercises) — your process is your own, so
there's no fixed expected output to compare against. Instead, self-check against `../rubric.md`
directly:

- Does it run end-to-end on a clean checkout, without manual fix-ups?
- Does it survive at least one deliberately bad input (a missing field, an unreachable page
  element, an unreadable document) without an unhandled crash?
- Is `bot.log` readable and does it actually tell you what happened, including for the failure
  case above?
- Run it twice in a row — does the second run do something sensible (not blindly redo/duplicate
  everything), the way Sessions 4/7/8's bots did?

Write your 1-page write-up (per `../spec.md`) after your bot is working, not before — it's much
easier to describe real design decisions and real limitations than planned ones.
