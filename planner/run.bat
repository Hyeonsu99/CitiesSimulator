@echo off
setlocal
cd /d "%~dp0"
echo [K-City Planner] Starting...

call py -3 --version >nul 2>&1
if not errorlevel 1 (
    call py -3 "%~dp0main.py"
    goto finished
)

set "PY_FALLBACK=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%PY_FALLBACK%" (
    "%PY_FALLBACK%" "%~dp0main.py"
    goto finished
)

call python --version >nul 2>&1
if not errorlevel 1 (
    call python "%~dp0main.py"
    goto finished
)

echo [ERROR] Python 3 was not found. Install Python 3 and try again.
pause
exit /b 1

:finished
if errorlevel 1 (
    echo [ERROR] The simulator failed to start. See the error above.
    pause
    exit /b 1
)
exit /b 0
