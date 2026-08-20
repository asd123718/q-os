#!/bin/bash
cd "$(dirname "$0")"
cat bundle/k*.js > KetOS.js
open "KetOS.html"
