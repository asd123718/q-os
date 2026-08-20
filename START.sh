#!/bin/bash
cd "$(dirname "$0")"
xdg-open "KetOS.html" 2>/dev/null || open "KetOS.html" 2>/dev/null || python3 -m webbrowser "KetOS.html"
