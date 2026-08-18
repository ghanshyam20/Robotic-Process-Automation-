# CLAUDE.md — RPA Course Setup Repo

This repo is **public and student-facing**. It contains installation/setup instructions only.

## Hard constraints

- **Nothing exercise-, solution-, or assignment-related goes here.** No code exercises, no
  solutions, no assignment specs, no slide content. If you're about to add anything beyond
  "how do I get my machine ready," stop and flag it — it belongs in the private `rpa-course` repo
  instead.
- **No institute-internal information.** No intranet URLs, no student data, no instructor contact
  details beyond what's already public. Assume anyone on the internet can and will read this repo.
- **Cross-platform parity is mandatory.** `macos-setup.md` and `windows-setup.md` must cover
  exactly the same toolset, kept in sync when either changes.
- **Keep it copy-pasteable.** Every command should be runnable as-is. Prefer official installers /
  winget / brew over anything requiring manual downloads, except where there's no alternative
  (e.g. Tesseract on Windows).
- **`verify_setup.py` must work identically on macOS and Windows** and print a clear PASS/FAIL per
  tool, not just crash on the first missing dependency.

## Contents

- `README.md` — what this repo is, who it's for, link back to the course
- `macos-setup.md`, `windows-setup.md` — install steps
- `verify_setup.py` — end-to-end environment check
- `troubleshooting.md` — known failure modes and fixes

## Toolset covered (fixed — confirm with instructor before changing)

Python 3.11+, git, VS Code, Playwright, Tesseract OCR, Ollama. All LLM inference is local via
Ollama's local API — no external/hosted API SDKs are part of this course, so none should appear
in these setup instructions.
