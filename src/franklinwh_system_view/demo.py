"""See the System view without a bridge: ``python -m franklinwh_system_view.demo [fixture] [port]``.

Serves a stand-in "standard dashboard" with a System view button, the overlay's files,
and ``/api/system`` built from one of the shipped example payloads.
"""
from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import build, fixture, static_dir

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>System view demo</title><link rel="stylesheet" href="/system-view/system-view.css">
<style>body{font-family:system-ui,sans-serif;margin:0;padding:16px;background:#121924;color:#e4e9f0}</style></head>
<body><header style="display:flex;gap:12px;align-items:center"><h1 style="margin:0;font-size:1.2rem">Standard dashboard</h1>
<button id="open" type="button">System view</button></header>
<p>This stands in for a bridge's own dashboard.</p>
<script src="/system-view/system-view.js"></script>
<script>FWHSystemView.mount({endpoint: "/api/system" + location.search});
document.getElementById("open").onclick = () => FWHSystemView.open();</script></body></html>"""


def make_handler(default: str):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _send(self, code, body, ctype):
            data = body if isinstance(body, bytes) else body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urlparse(self.path)
            if u.path == "/":
                return self._send(200, PAGE, "text/html; charset=utf-8")
            if u.path == "/favicon.ico":
                return self._send(204, b"", "image/x-icon")
            if u.path == "/api/system":
                name = parse_qs(u.query).get("fixture", [default])[0]
                try:
                    return self._send(200, json.dumps(build(fixture(name))), "application/json")
                except FileNotFoundError:
                    return self._send(404, json.dumps({"detail": f"no fixture {name!r}"}), "application/json")
            if u.path.startswith("/system-view/"):
                f = static_dir() / u.path.rsplit("/", 1)[-1]
                if f.is_file():
                    ctype = "text/css" if f.suffix == ".css" else "text/javascript"
                    return self._send(200, f.read_bytes(), ctype)
            return self._send(404, "not found", "text/plain")
    return H


def serve(default: str = "us_backup_no_solar", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(default))


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "us_backup_no_solar"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    print(f"http://127.0.0.1:{port}/  (fixture {name}; add ?fixture=<name> to switch)")
    serve(name, port).serve_forever()
