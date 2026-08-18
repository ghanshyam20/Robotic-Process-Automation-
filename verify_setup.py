"""Environment verification for the RPA course. Run after following macos-setup.md
or windows-setup.md. Prints a PASS/FAIL line per tool and never stops at the first
failure, so students get a full picture of what's still missing.
"""

import importlib
import shutil
import subprocess
import sys

results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((name, True, detail or "ok"))
    except Exception as exc:
        results.append((name, False, str(exc)))


def check_python_version():
    if sys.version_info < (3, 11):
        raise RuntimeError(f"found {sys.version.split()[0]}, need 3.11+")
    return sys.version.split()[0]


def check_command(cmd, version_args=("--version",)):
    path = shutil.which(cmd)
    if not path:
        raise RuntimeError(f"'{cmd}' not found on PATH")
    out = subprocess.run(
        [cmd, *version_args], capture_output=True, text=True, timeout=15
    )
    return out.stdout.strip().splitlines()[0] if out.stdout else path


def check_import(module):
    mod = importlib.import_module(module)
    return getattr(mod, "__version__", "importable")


def check_playwright_browsers():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        browser.close()
    return "chromium launches"


def check_tesseract_binding():
    import pytesseract

    return f"tesseract {pytesseract.get_tesseract_version()}"


def check_ollama_daemon():
    import ollama

    models = ollama.list()
    count = len(models.get("models", []))
    return f"daemon reachable, {count} model(s) pulled"


check("Python >= 3.11", check_python_version)
check("git", lambda: check_command("git"))
check("Tesseract OCR binary", lambda: check_command("tesseract"))
check("Ollama binary", lambda: check_command("ollama"))
check("Python package: playwright", lambda: check_import("playwright"))
check("Playwright Chromium browser", check_playwright_browsers)
check("Python package: rpaframework", lambda: check_import("RPA.Excel.Files"))
check("Python package: pytesseract", lambda: check_import("pytesseract"))
check("pytesseract <-> tesseract binding", check_tesseract_binding)
check("Python package: ollama (client)", lambda: check_import("ollama"))
check("Ollama daemon reachable", check_ollama_daemon)
check("Python package: pytest", lambda: check_import("pytest"))

name_width = max(len(name) for name, _, _ in results)
all_passed = True
for name, ok, detail in results:
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_passed = False
    print(f"[{status}] {name.ljust(name_width)}  {detail}")

print()
if all_passed:
    print("All checks passed. You're ready for Session 2.")
    sys.exit(0)
else:
    print("Some checks failed — see troubleshooting.md for the failures above.")
    sys.exit(1)
