@echo off
title WASTECLEAN - AI-Driven Waste Management Platform
cd /d "%~dp0"
echo.
echo ==========================================
echo        WASTECLEAN DEMO LAUNCHER
echo ==========================================
echo.
if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo Could not create virtual environment.
        echo Make sure Python 3.10+ is installed.
        pause
        exit /b 1
    )
)
echo Installing/checking dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
echo.
echo Starting WASTECLEAN...
start "" http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
pause
