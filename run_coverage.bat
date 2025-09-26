@echo off
echo ============================================
echo Enhanced GitHub Coverage Generator v2.0
echo With LLM Integration for Non-Compatible Repos
echo ============================================
echo.

:: Set the script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or later
    pause
    exit /b 1
)

:: Install requirements if needed
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install/update requirements
echo Installing/updating requirements...
pip install -r requirements.txt

:: Run the enhanced coverage generator
if "%1"=="" (
    echo Using repository URL from config.ini...
    python generate_coverage.py
) else (
    echo Using repository URL: %1
    python generate_coverage.py %1
)

:: Check exit code
if errorlevel 1 (
    echo.
    echo ERROR: Coverage generation failed!
    pause
    exit /b 1
)

echo.
echo SUCCESS: Coverage report generated!
echo Opening report in browser...

:: Open the coverage report
start "" "coverage_output\index.html"

pause