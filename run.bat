@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Starting ThaiWord on http://localhost:8082 ...
python run.py
pause
