@echo off
setlocal

cd /d "%~dp0"

echo Installing Monitoring Agent dependencies...
python -m pip install -r requirements.txt

echo.
echo Installation completed.
echo Edit config.yaml if this client uses different log file paths.
echo Run start_agent.bat for development mode.
echo Run build_agent.bat to create dist\agent.exe.
pause
