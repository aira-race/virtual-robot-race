@echo off
if not exist .venv (
    echo ERROR: Virtual environment not found.
    echo Please run setup_env.bat first.
    pause
    exit /b 1
)
call .venv\Scripts\activate
python main.py
