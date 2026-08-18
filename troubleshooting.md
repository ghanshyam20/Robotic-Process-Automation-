# Troubleshooting

Common failure modes from `verify_setup.py`, grouped by tool.

## PATH issues

- **`'tesseract' not found on PATH` (Windows)** — the UB-Mannheim installer doesn't always add
  itself to PATH. Add the install folder (default `C:\Program Files\Tesseract-OCR`) to your user
  PATH, then open a **new** PowerShell window. If you don't want to touch PATH, set it explicitly
  in code instead:
  ```python
  import pytesseract
  pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```
- **`'git' not found` / `'ollama' not found` right after install** — same cause on both OSes:
  the shell that ran the installer hasn't picked up the updated PATH yet. Close and reopen your
  terminal (Terminal.app / PowerShell) and try again before assuming the install failed.
- **`Activate.ps1 cannot be loaded` (Windows)** — execution policy is blocking the venv activation
  script, not a broken install. Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once,
  then retry.

## Playwright browser download failures behind the institute firewall

`playwright install` downloads browser binaries (~100–300MB) directly from Playwright's CDN,
which institute networks sometimes block or throttle.

- Try again on the institute guest/eduroam Wi-Fi rather than a wired lab connection, or vice
  versa — firewall rules sometimes differ between them.
- If it still fails, try tethering to a phone hotspot once just to complete `playwright install`
  — after that, the binaries are cached locally in `~/.cache/ms-playwright` (macOS/Linux) or
  `%USERPROFILE%\AppData\Local\ms-playwright` (Windows) and no further downloads are needed.
- If downloads are consistently blocked, flag it to the instructor before Session 5 — a shared
  offline install bundle may be needed for the whole class.

## Ollama model pull size / time

- `ollama pull llama3.1:8b` downloads several GB and can take a long time on institute Wi-Fi.
  **Start the pull before Session 2 ends**, not during a later session — it can run in the
  background while you do other setup steps.
- Check free disk space first (`df -h` on macOS, `Get-PSDrive C` on Windows) — you need the model
  size plus working headroom; a failed pull often silently leaves a partial model. If
  `verify_setup.py` reports 0 models pulled after a pull you thought succeeded, re-run
  `ollama pull llama3.1:8b` — it resumes rather than restarting from zero.
- If your machine doesn't have enough RAM/disk for the standard model, flag it to the instructor
  — a smaller model may be substituted for you rather than blocking your setup.

## `pytesseract <-> tesseract binding` fails but the binary check passed

This means the `tesseract` command works in your terminal but `pytesseract` (the Python package)
can't find it — usually because pytesseract is running in a virtual environment whose PATH
differs slightly. Re-check the venv is activated (prompt should show `(.venv)`) and, on Windows,
set `pytesseract.pytesseract.tesseract_cmd` explicitly as shown above.

## Still stuck?

Bring the exact `verify_setup.py` output to Session 2 — the guided setup lab is built around
diagnosing exactly these failures live.
