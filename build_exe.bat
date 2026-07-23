@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building Zaza Assistant Executable...
echo This might take a few minutes...
pyinstaller --name "Zaza Assistant" ^
            --windowed ^
            --noconsole ^
            --hidden-import PyQt6 ^
            --hidden-import pyaudio ^
            --hidden-import speech_recognition ^
            --hidden-import psutil ^
            --hidden-import pycaw ^
            --collect-all openwakeword ^
            --collect-all faster_whisper ^
            --collect-all ctranslate2 ^
            --collect-data onnxruntime ^
            --add-data ".env;." ^
            main.py

echo.
echo Build Complete!
echo You can find your executable inside the "dist\Zaza Assistant" folder.
pause
