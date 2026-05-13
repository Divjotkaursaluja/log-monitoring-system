@echo off
setlocal

cd /d "%~dp0"

echo Building Windows agent executable...
python -m pip install -r requirements.txt
python -m PyInstaller --onefile --name agent --add-data "config.yaml;." agent.py
copy /Y config.yaml dist\config.yaml

echo.
echo Build complete: dist\agent.exe
echo Runtime config copied to dist\config.yaml
pause
