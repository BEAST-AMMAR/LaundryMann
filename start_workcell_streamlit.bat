@echo off
echo ===================================================
echo Launching Industrial Workcell Telemetry Console
echo ===================================================
call .venv\Scripts\activate.bat 2>nul
streamlit run streamlit_app.py --server.port 8501
pause
