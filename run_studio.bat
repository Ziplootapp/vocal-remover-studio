@echo off
title ziploot.app AI Vocal Separator Studio Launcher
echo ========================================================
echo  ziploot.app - Free AI Vocal & Music Separator Studio
echo ========================================================
echo.
echo Installing/Verifying Python AI Packages...
python -m pip install -r requirements.txt
echo.
echo Starting Multi-Threaded AI Studio on http://localhost:5001 ...
start http://localhost:5001
python app.py
pause
