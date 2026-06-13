#!/usr/bin/env python3
"""
Proxy local para fixture_mundial2026.html
Sirve archivos estáticos en / y reenvía /api/* a api.football-data.org
evitando el bloqueo CORS del navegador.

Uso: python3 proxy.py [puerto]   (default: 8888)
"""

import sys
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

FD_TOKEN = '3e4b72d3488e4e1c81f23edf0eb1c7ec'
FD_BASE  = 'https://api.football-data.org'


class ProxyHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith('/api/'):
            self._proxy_api()
        else:
            super().do_GET()

    def _proxy_api(self):
        # /api/v4/... → https://api.football-data.org/v4/...
        upstream = FD_BASE + self.path[len('/api'):]
        req = urllib.request.Request(upstream, headers={'X-Auth-Token': FD_TOKEN})
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
    server = HTTPServer(('0.0.0.0', port), ProxyHandler)
    print(f"Proxy corriendo en http://localhost:{port}/")
    print(f"Abre: http://localhost:{port}/fixture_mundial2026.html")
    print("Ctrl+C para detener.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")
