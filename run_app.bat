@echo off
title AirAssist – AI-Powered Air Quality Monitoring
cd /d "%~dp0"
echo ========================================================
echo    AirAssist – AI Air Quality & Health Advisory System
echo ========================================================
echo    Starting Flask Server on http://127.0.0.1:5000 ...
echo    Open http://127.0.0.1:5000 in your browser!
echo ========================================================
python app.py
pause
