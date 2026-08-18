# Windows Setup

Run these in PowerShell (as your normal user, not admin, unless a step says otherwise).

## 1. Python 3.11+
```powershell
winget install Python.Python.3.11
python --version
```

## 2. Git & VS Code
```powershell
winget install Git.Git
winget install Microsoft.VisualStudioCode
```

## 3. Project environment
```powershell
cd path\to\this\repo
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r shared\requirements.txt
```
> If `Activate.ps1` is blocked by execution policy, run:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 4. Playwright
```powershell
pip install playwright
playwright install
```

## 5. Tesseract OCR
Download and run the installer from the UB-Mannheim build:
https://github.com/UB-Mannheim/tesseract/wiki

**Important:** during install, note the install path (default
`C:\Program Files\Tesseract-OCR`) and add it to your PATH, or set it explicitly in code:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## 6. Ollama
Download and run the installer from https://ollama.com
```powershell
ollama --version
ollama pull llama3.1:8b   # confirm model choice/size with instructor
```

## 7. Verify everything
```powershell
python setup\verify_setup.py
```
All checks should print PASS. If something fails, see `setup\troubleshooting.md`.
