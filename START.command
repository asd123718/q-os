#!/bin/bash
cd "$(dirname "$0")"
if [ ! -f "./KetOS.html" ]; then
  echo "KetOS.html not found."
  exit 1
fi
open "./KetOS.html"
