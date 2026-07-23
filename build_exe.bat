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
            main.py

echo.
echo Build Complete!
echo You can find your executable inside the "dist\Zaza Assistant" folder.
echo NOTE: You need to copy your .env file into the "dist\Zaza Assistant" folder so the exe can read your settings!
pause
