@echo off
echo Starting Nexus Laundry AI Dashboard...
python -m uvicorn api:app --port 8000
pause
