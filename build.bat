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
    --collect-all vosk ^
    main.py

echo.
echo Build complete. Copying required files next to the .exe ...

REM models/ and config.py's app paths must sit next to the exe, not inside it,
REM since VOSK_MODEL_PATH resolves relative to the exe's location at runtime.
xcopy /E /I /Y models dist\models

echo.
echo Done. Your app is at: dist\ZazaAssistant.exe
echo The models\vosk-model-small-en-us folder must stay next to it.
echo.
echo Next: run setup_task_scheduler.bat to make it launch at login.
pause
