#!/bin/sh
cd "$(dirname "$0")"
if [ ! -f "./KetOS.html" ]; then
  echo "KetOS.html not found."
  exit 1
fi
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "./KetOS.html"
elif command -v open >/dev/null 2>&1; then
  open "./KetOS.html"
elif command -v wslview >/dev/null 2>&1; then
  wslview "./KetOS.html"
elif command -v python3 >/dev/null 2>&1; then
  python3 -m webbrowser "./KetOS.html"
else
  echo "Open KetOS.html in your browser."
fi
