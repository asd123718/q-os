#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f "./KetOS.html" ] || [ ! -f "./ketos.js" ]; then
  echo "KetOS.html and ketos.js must be in this folder."
  exit 1
fi
open "./KetOS.html"
