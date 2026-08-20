#!/bin/sh
cd "$(dirname "$0")"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "./KetOS.html"
elif command -v open >/dev/null 2>&1; then
  open "./KetOS.html"
else
  echo "Open KetOS.html in your browser"
fi
