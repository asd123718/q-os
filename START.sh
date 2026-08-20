#!/bin/sh
set -eu
cd "$(dirname "$0")"
export KETOS_ROOT="$(pwd)"
PY="$KETOS_ROOT/runtime/py/bin/python3"
if [ ! -x "$PY" ]; then
  mkdir -p runtime
  TAR=""
  UNAME="$(uname -s)"
  ARCH="$(uname -m)"
  case "$UNAME" in
    Linux) TAR="runtime/cpython-3.12.14-linux-x86_64.tar.gz" ;;
    Darwin)
      if [ "$ARCH" = "arm64" ]; then TAR="runtime/cpython-3.12.14-darwin-arm64.tar.gz"
      else TAR="runtime/cpython-3.12.14-darwin-x64.tar.gz"; fi
      ;;
    *) echo "Unsupported OS: $UNAME"; exit 1 ;;
  esac
  if [ ! -f "$TAR" ]; then
    echo "Missing bundled interpreter: $TAR"
    exit 1
  fi
  echo "Extracting bundled CPython 3.12.14..."
  tar -xzf "$TAR" -C runtime
  rm -rf runtime/py
  mv runtime/python runtime/py
fi
if ! "$PY" -c "import numpy" >/dev/null 2>&1; then
  echo "Installing bundled numpy (offline)..."
  "$PY" -m pip install --disable-pip-version-check --no-index --find-links "$KETOS_ROOT/runtime/wheels" --no-deps numpy
fi
export KETOS_HOST="${KETOS_HOST:-127.0.0.1}"
export KETOS_PORT="${KETOS_PORT:-8080}"
export KETOS_QUIET="${KETOS_QUIET:-1}"
exec "$PY" -B "$KETOS_ROOT/ketos/server.py"
