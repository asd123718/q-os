@echo off
cd /d "%~dp0"
copy /b "%~dp0bundle\k00.js"+"%~dp0bundle\k01.js"+"%~dp0bundle\k02.js"+"%~dp0bundle\k03.js"+"%~dp0bundle\k04.js"+"%~dp0bundle\k05.js"+"%~dp0bundle\k06.js"+"%~dp0bundle\k07.js" "%~dp0KetOS.js" >nul
start "" "%~dp0KetOS.html"
