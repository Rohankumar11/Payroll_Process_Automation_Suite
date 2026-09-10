@echo off
title Payroll Process Automation Suite
cd /d "%~dp0"

echo ============================================================
echo   PAYROLL PROCESS AUTOMATION SUITE
echo   First run installs dependencies (2-5 minutes).
echo   Later runs start instantly.
echo ============================================================
echo.

REM ---------- create virtual environment if missing ----------
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating Python environment...
    python -m venv .venv
    if errorlevel 1 (
        py -3 -m venv .venv
        if errorlevel 1 (
            echo.
            echo ERROR: Python not found.
            echo Install Python 3.10 or newer from https://python.org
            echo and tick "Add Python to PATH" during installation.
            pause
            exit /b 1
        )
    )
) else (
    echo [1/3] Python environment found.
)

REM ---------- install dependencies ----------
echo [2/3] Checking dependencies...
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: dependency installation failed.
    echo Check internet / proxy connection and run this file again.
    pause
    exit /b 1
)

REM ---------- launch ----------
echo [3/3] Starting application...
echo.
echo The app will open in your browser at  http://localhost:8501
echo Keep this black window open while using the application.
echo.
".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501

pause