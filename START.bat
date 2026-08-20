@echo off
setlocal
cd /d "%~dp0"
if not exist "KetOS.html" (
  echo KetOS.html not found.
  pause
  exit /b 1
)
if not exist "ketos.js" (
  echo ketos.js not found. Keep it next to KetOS.html.
  pause
  exit /b 1
)
start "" "%~dp0KetOS.html"
