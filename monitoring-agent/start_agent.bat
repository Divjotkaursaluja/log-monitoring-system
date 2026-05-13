@echo off
setlocal

cd /d "%~dp0"

echo Starting Monitoring Agent in development mode...
python agent.py

pause
