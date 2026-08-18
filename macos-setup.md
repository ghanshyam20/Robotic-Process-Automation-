# macOS Setup

Run these in Terminal. Requires [Homebrew](https://brew.sh) — install it first if you don't have it.

## 1. Python 3.11+
```bash
brew install python@3.11
python3.11 --version
```

## 2. Git & VS Code
```bash
brew install git
brew install --cask visual-studio-code
```

## 3. Project environment
```bash
cd path/to/this/repo
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r shared/requirements.txt   # or: pip install -e shared (if using pyproject)
```

## 4. Playwright
```bash
pip install playwright
playwright install
```

## 5. Tesseract OCR
```bash
brew install tesseract
tesseract --version
```

## 6. Ollama
```bash
brew install ollama
# or download the app from https://ollama.com
ollama --version
ollama pull llama3.1:8b   # or whichever model the course standardizes on — confirm size/RAM fit
```

## 7. Verify everything
```bash
python setup/verify_setup.py
```
All checks should print PASS. If something fails, see `setup/troubleshooting.md`.
