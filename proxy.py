#!/usr/bin/env python3
"""
Proxy local para fixture_mundial2026.html

Sirve archivos estáticos en / y reenvía /api/* a api.football-data.org
evitando el bloqueo CORS del navegador. El token se lee de config.js, que
está en .gitignore, para que no viaje al repositorio.

Uso: python3 proxy.py [puerto]   (default: 8888)
"""

import re
import sys
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

FD_BASE = 'https://api.football-data.org'


def read_token():
    """Lee FD_TOKEN desde config.js (el mismo archivo que consume el navegador)."""
    cfg = Path(__file__).with_name('config.js')
    if not cfg.exists():
        return None
    m = re.search(r"""FD_TOKEN\s*=\s*['"]([^'"]+)['"]""", cfg.read_text())
    return m.group(1) if m else None


class ProxyHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith('/api/'):
            self._proxy_api()
        else:
            super().do_GET()

    def _proxy_api(self):
        token = read_token()
        if not token or token == 'TU_TOKEN_AQUI':
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'Falta el token en config.js. '
                         'Copia config.example.js y pega el tuyo de football-data.org'
            }).encode())
            return

        # /api/v4/... → https://api.football-data.org/v4/...
        upstream = FD_BASE + self.path[len('/api'):]
        req = urllib.request.Request(upstream, headers={'X-Auth-Token': token})
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} — {fmt % args}")


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    if not read_token():
        print("⚠️  No encontré FD_TOKEN en config.js — la app va a mostrar el error de token.\n")
    server = HTTPServer(('0.0.0.0', port), ProxyHandler)
    print(f"Proxy corriendo en http://localhost:{port}/")
    print(f"Abre: http://localhost:{port}/fixture_mundial2026.html")
    print("Ctrl+C para detener.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")
