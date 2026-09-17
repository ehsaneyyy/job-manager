@echo off
setlocal
set ROOT=%~dp0..
echo ============================================
echo  Job Manager Setup
echo ============================================
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found. Install Python from https://www.python.org/downloads
    echo and tick "Add python.exe to PATH", then run this script again.
    pause
    exit /b 1
)
cd "%ROOT%\backend"
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)
echo Installing dependencies...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Installing browser for job automation...
playwright install chromium
if not exist ".env" (
    echo Creating .env from example...
    copy ".env.example" ".env" >nul
    echo.
    echo IMPORTANT: open backend\.env and set:
    echo   - API_KEY to a long random string
    echo   - LLM_API_KEY and LLM_MODEL from free providers
    echo     - OpenRouter:  https://openrouter.ai
    echo     - Groq:        https://console.groq.com
    echo     - Gemini:      https://aistudio.google.com
)
echo.
echo Setup complete. Run run.bat to start the server.
pause