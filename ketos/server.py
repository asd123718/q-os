#!/usr/bin/env python3
"""Ket OS desktop server — CPython kernel, stdlib only."""

from __future__ import annotations

import json
import os
import sys
import threading
import traceback
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(os.environ.get("KETOS_ROOT") or Path(__file__).resolve().parent.parent)
UI = ROOT / "ui"
HOST = os.environ.get("KETOS_HOST", "127.0.0.1")
PORT = int(os.environ.get("KETOS_PORT", "8080"))
QUIET = os.environ.get("KETOS_QUIET", "1") not in ("0", "false", "no")

# Make `import ketos` work when launched as a script.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ketos.kernel import get_engine  # noqa: E402

ENGINE = get_engine()

# Windows Chrome aborts keep-alive sockets: WinError 10053 / 10054.
_HANGUP = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError, ConnectionError)
_WINERR = {10053, 10054, 10038, 10057, 10058, 64, 232}
_ERRNO = {32, 54, 104}  # EPIPE / ECONNRESET


def _is_hangup(exc: BaseException | None) -> bool:
    if exc is None:
        return False
    if isinstance(exc, _HANGUP):
        return True
    if isinstance(exc, OSError):
        if getattr(exc, "winerror", None) in _WINERR:
            return True
        if getattr(exc, "errno", None) in _ERRNO:
            return True
    return False


class Handler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 8
    disable_nagle_algorithm = True

    def log_message(self, fmt: str, *args) -> None:
        if QUIET:
            return
        try:
            sys.stderr.write("[ketos] " + (fmt % args) + "\n")
        except OSError:
            pass

    def log_error(self, fmt: str, *args) -> None:
        msg = fmt % args if args else str(fmt)
        if any(s in msg for s in ("10053", "10054", "Broken pipe", "Connection reset", "Connection aborted")):
            return
        if QUIET:
            return
        super().log_error(fmt, *args)

    def handle(self) -> None:
        try:
            super().handle()
        except Exception as exc:
            if _is_hangup(exc):
                self.close_connection = True
                return
            raise

    def handle_one_request(self) -> None:
        try:
            super().handle_one_request()
        except Exception as exc:
            if _is_hangup(exc):
                self.close_connection = True
                return
            raise

    def finish(self) -> None:
        try:
            super().finish()
        except Exception as exc:
            if _is_hangup(exc):
                return
            raise

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.close_connection = True
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            if _is_hangup(exc):
                self.close_connection = True
                return
            raise

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.close_connection = True
        try:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Connection", "close")
            self.end_headers()
        except Exception as exc:
            if _is_hangup(exc):
                return
            raise

    def do_GET(self) -> None:  # noqa: N802
        try:
            path = unquote(urlparse(self.path).path)
            if path in ("/", "/index.html", "/KetOS.html"):
                data = (UI / "index.html").read_bytes()
                return self._send(200, data, "text/html; charset=utf-8")
            if path == "/api/status":
                body = json.dumps(ENGINE.status(), ensure_ascii=False).encode()
                return self._send(200, body, "application/json; charset=utf-8")
            rel = path.lstrip("/")
            candidate = (UI / rel).resolve()
            try:
                candidate.relative_to(UI.resolve())
            except ValueError:
                return self._send(403, b"forbidden", "text/plain")
            if candidate.is_file():
                ext = candidate.suffix.lower()
                ctypes = {
                    ".js": "text/javascript; charset=utf-8",
                    ".css": "text/css; charset=utf-8",
                    ".html": "text/html; charset=utf-8",
                    ".svg": "image/svg+xml",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".webp": "image/webp",
                }
                return self._send(200, candidate.read_bytes(), ctypes.get(ext, "application/octet-stream"))
            self._send(404, b"not found", "text/plain")
        except Exception as exc:
            if _is_hangup(exc):
                self.close_connection = True
                return
            raise

    def do_POST(self) -> None:  # noqa: N802
        try:
            path = urlparse(self.path).path
            if path not in ("/api/ket", "/api/op"):
                return self._send(404, b"not found", "text/plain")
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b"{}"
            req = json.loads(raw.decode("utf-8") or "{}")
            result = ENGINE.handle(req if isinstance(req, dict) else {"op": "status"})
            body = json.dumps(result, ensure_ascii=False).encode()
            self._send(200, body, "application/json; charset=utf-8")
        except Exception as exc:
            if _is_hangup(exc):
                self.close_connection = True
                return
            err = {"error": str(exc), "trace": traceback.format_exc()}
            try:
                self._send(400, json.dumps(err).encode(), "application/json; charset=utf-8")
            except Exception as send_exc:
                if _is_hangup(send_exc):
                    return
                raise


class QuietServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 64

    def handle_error(self, request, client_address) -> None:  # noqa: ARG002
        if _is_hangup(sys.exc_info()[1]):
            return
        # Don't dump hangups; still print real bugs.
        super().handle_error(request, client_address)


def main() -> None:
    host = HOST
    port = PORT
    httpd = QuietServer((host, port), Handler)
    url = f"http://127.0.0.1:{port}/" if host in ("0.0.0.0", "::") else f"http://{host}:{port}/"
    print(f"Ket OS  CPython {ENGINE.version}  numpy {ENGINE.status().get('numpy')}  {url}", flush=True)
    print(f"backend {ENGINE.backend_label}  engine {ENGINE.status()['engine']}  {ENGINE.n}q float64  {ENGINE.status()['sv_bytes']} bytes", flush=True)
    print("Close this window to stop Ket OS.", flush=True)
    if os.environ.get("KETOS_NO_BROWSER") not in ("1", "true", "yes"):
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped", flush=True)


if __name__ == "__main__":
    main()
