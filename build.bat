@echo off
REM Zaza Assistant — Build Script
REM Packages main.py into a standalone .exe with PyInstaller.
REM Run this from inside the activated venv: build.bat

echo Building ZazaAssistant.exe ...

pyinstaller --onefile --noconsole --name ZazaAssistant ^
    --hidden-import=vosk ^
    --hidden-import=sounddevice ^
    --hidden-import=pyttsx3.drivers ^
    --hidden-import=pyttsx3.drivers.sapi5 ^
    --hidden-import=faster_whisper ^
    --hidden-import=ctranslate2 ^
    --hidden-import=openwakeword ^
    --hidden-import=pyperclip ^
    --hidden-import=pycaw ^
    --hidden-import=pycaw.pycaw ^
    --hidden-import=comtypes ^
    --collect-all vosk ^
    --collect-all openwakeword ^
    --collect-all ctranslate2 ^
    main.py

echo.
echo Build complete. Copying required files next to the .exe ...

REM models/ folder kept for potential future use (Vosk fallback)
if exist models xcopy /E /I /Y models dist\models

echo.
echo Done. Your app is at: dist\ZazaAssistant.exe
echo.
echo Next: run setup_task_scheduler.bat to make it launch at login.
pause
