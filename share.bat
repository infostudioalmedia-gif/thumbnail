@echo off
chcp 65001 >nul
cd /d "%~dp0"
where cloudflared >nul 2>&1
if errorlevel 1 (
  echo cloudflared غير مثبت. ثبّته مرة واحدة بالأمر:
  echo     winget install Cloudflare.cloudflared
  echo ثم اقفل النافذة دي وشغّل share.bat تاني.
  pause
  exit /b
)
REM وضع المشاركة: بدون مسارات الجهاز (حماية ملفاتك)
set ROOYA_CLOUD=1
set ROOYA_HOST=127.0.0.1
start "Rooya server" /min .venv\Scripts\python app.py
timeout /t 5 >nul
echo ======================================================
echo  هيظهر تحت رابط بيبدأ بـ https:// وينتهي بـ trycloudflare.com
echo  ده الرابط اللي تبعته. سيب النافذة دي مفتوحة طول ما عايز الرابط يشتغل.
echo ======================================================
cloudflared tunnel --url http://127.0.0.1:5055
