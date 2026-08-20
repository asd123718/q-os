#!/bin/bash
cd "$(dirname "$0")"
cat bundle/k*.js > KetOS.js
if command -v xdg-open >/dev/null 2>&1; then xdg-open "KetOS.html"
elif command -v open >/dev/null 2>&1; then open "KetOS.html"
else python3 -m webbrowser "KetOS.html" 2>/dev/null || true
fi
