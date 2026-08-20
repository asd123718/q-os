@echo off
setlocal
cd /d "%~dp0"
set KETOS_ROOT=%~dp0
if exist "runtime\py\python.exe" goto run
if not exist "runtime\cpython-3.12.14-windows-x86_64.tar.gz" (
  echo Missing bundled interpreter: runtime\cpython-3.12.14-windows-x86_64.tar.gz
  pause
  exit /b 1
)
echo Extracting bundled CPython 3.12.14...
if not exist runtime mkdir runtime
tar -xf "runtime\cpython-3.12.14-windows-x86_64.tar.gz" -C runtime
if exist runtime\py rmdir /s /q runtime\py
move runtime\python runtime\py
:run
set KETOS_HOST=127.0.0.1
set KETOS_PORT=8080
"runtime\py\python.exe" -B "%~dp0ketos\server.py"
if errorlevel 1 pause
