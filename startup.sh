#!/bin/sh
set -eu
cd /workspace
python3 -c "import qiskit" >/dev/null 2>&1 || pip3 install --user 'qiskit>=1.2,<3' numpy
if curl -sf -o /dev/null --max-time 2 http://127.0.0.1:8080/; then
  exit 0
fi
npm run dev >>/tmp/app-startup.log 2>&1 &
