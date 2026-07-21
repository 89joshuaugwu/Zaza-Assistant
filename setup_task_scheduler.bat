@echo off
REM Zaza Assistant — Task Scheduler Setup
REM Registers the built .exe to launch silently at login and restart on crash.
REM Run this AFTER build.bat has produced dist\ZazaAssistant.exe
REM Right-click this file -> "Run as administrator" (needed to register the task)

set EXE_PATH=%~dp0dist\ZazaAssistant.exe

if not exist "%EXE_PATH%" (
    echo ERROR: %EXE_PATH% not found. Run build.bat first.
    pause
    exit /b 1
)

echo Registering scheduled task "ZazaAssistant" ...

schtasks /Create /TN "ZazaAssistant" ^
    /TR "\"%EXE_PATH%\"" ^
    /SC ONLOGON ^
    /RL LIMITED ^
    /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Success. Zaza will now launch automatically every time you log in.
    echo To test it right now without restarting: schtasks /Run /TN "ZazaAssistant"
    echo To remove it later: schtasks /Delete /TN "ZazaAssistant" /F
) else (
    echo.
    echo Something went wrong. Make sure you ran this as Administrator.
)

pause
