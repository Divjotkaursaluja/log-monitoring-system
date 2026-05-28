@echo off
setlocal

cd /d "%~dp0"

if not exist "dist\agent.exe" (
  echo dist\agent.exe was not found.
  echo Run build_agent.bat first.
  pause
  exit /b 1
)

if exist client-package rmdir /S /Q client-package
mkdir client-package

copy /Y dist\agent.exe client-package\agent.exe
copy /Y dist\config.yaml client-package\config.yaml

echo.
echo Client package created:
echo monitoring-agent\client-package\agent.exe
echo monitoring-agent\client-package\config.yaml
echo.
echo Do not include agent_state.json or buffered_logs.jsonl in first-time client packages.
pause
