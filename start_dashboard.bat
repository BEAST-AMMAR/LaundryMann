@echo off
echo ===================================================
echo Starting NEXUS Autonomous Robotic Laundry Workcell
echo ===================================================
call .venv\Scripts\activate.bat 2>nul
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
pause
