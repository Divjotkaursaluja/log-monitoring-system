@echo off
setlocal

cd /d "%~dp0"

if not exist "dist\agent.exe" (
  echo dist\agent.exe was not found.
  echo Run build_agent.bat first.
  pause
  exit /b 1
)

echo Installing AI Log Monitoring Agent as a Windows service...
sc create AILogMonitoringAgent binPath= "\"%~dp0dist\agent.exe\"" start= auto DisplayName= "AI Log Monitoring Agent"
sc description AILogMonitoringAgent "Collects local application logs and forwards them securely to the AI Powered Log Monitoring backend."
sc start AILogMonitoringAgent

echo.
echo Service installed and started.
pause
