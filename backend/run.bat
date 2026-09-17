@echo off
setlocal
cd "%~dp0..\backend"
if not exist ".venv" (
    echo Virtual environment missing. Run setup.bat first.
    pause
    exit /b 1
)
call ".venv\Scripts\activate.bat"
echo Starting Job Manager server on http://127.0.0.1:8765
uvicorn app.main:app --host 0.0.0.0 --port 8765
pause