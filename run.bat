@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv ( python -m venv .venv & .venv\Scripts\python -m pip install -q flask gdown pillow "opencv-python-headless<5" numpy arabic-reshaper python-bidi fonttools yt-dlp )
.venv\Scripts\python app.py
pause
