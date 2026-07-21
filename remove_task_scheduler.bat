@echo off
REM Removes the ZazaAssistant scheduled task. Run as administrator.
schtasks /Delete /TN "ZazaAssistant" /F
echo.
echo Removed. Zaza will no longer launch at login.
pause
