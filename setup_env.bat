@echo off
REM ===== Virtual Robot Race - Environment Setup =====
REM Requires: Python 3.12 or later (64-bit)
REM   https://www.python.org/downloads/
REM   IMPORTANT: Check "Add Python to PATH" during installation

REM ===== Step 1: Create virtual environment =====
echo Detected Python:
python --version
where python
echo.
python -m venv .venv
if errorlevel 1 (
    echo.
    echo ERROR: Failed to create virtual environment.
    echo   - Is Python 3.12+ installed?
    echo   - Was "Add Python to PATH" checked during installation?
    echo   - Windows Store Python is NOT supported. Install from python.org instead.
    echo   - If Anaconda/Miniconda is installed, open "Anaconda Prompt" and run this script there.
    echo.
    pause
    exit /b 1
)

REM ===== Step 2: Upgrade pip =====
call .venv\Scripts\python.exe -m pip install --upgrade pip

REM ===== Step 3: Install requirements =====
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some packages.
    echo   - Network issue? Check your internet connection and try again.
    echo   - torch/torchvision failed? Do NOT run pip install manually.
    echo     Just re-run this script. If it keeps failing, check:
    echo     https://github.com/aira-race/virtual-robot-race/issues
    echo.
    pause
    exit /b 1
)

REM ===== Step 4: Configure VS Code to use .venv automatically =====
if not exist .vscode mkdir .vscode
(
    echo {
    echo     "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    echo     "python.terminal.activateEnvironment": true
    echo }
) > .vscode\settings.json

REM ===== Step 5: Show Python version =====
echo.
echo =============================================
for /f "tokens=*" %%i in ('.venv\Scripts\python.exe --version') do echo %%i
echo Setup complete!
echo.
echo Next steps:
echo   1. Open config.txt and set your NAME
echo   2. Run: python main.py
echo =============================================

start cmd /k ".venv\Scripts\activate"
