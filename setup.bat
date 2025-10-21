@echo off
REM IQOS Social Intelligence - Windows Setup Script
REM Run this after cloning the repository

echo ====================================
echo IQOS Social Intelligence Setup
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/4] Verifying setup...
python run_analysis.py
if errorlevel 1 (
    echo.
    echo WARNING: Test run failed!
    echo Make sure you've copied the data files to:
    echo   - data\input\dataset_instagram-scraper_*.json
    echo   - data\images\*.jpg
    echo.
) else (
    echo.
    echo ====================================
    echo Setup Complete! 
    echo ====================================
    echo.
    echo To activate the environment in the future:
    echo   venv\Scripts\activate
    echo.
    echo To run the analysis:
    echo   python run_analysis.py
    echo.
)

pause