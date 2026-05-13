@echo off
setlocal

echo Stopping AI Log Monitoring Agent service...
sc stop AILogMonitoringAgent

echo Removing AI Log Monitoring Agent service...
sc delete AILogMonitoringAgent

echo.
echo Service removed.
pause
