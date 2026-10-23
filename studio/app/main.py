from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


APP_VERSION = "0.1.0"
PROJECTS_ROOT = Path(os.environ.get("PROJECTS_ROOT", "/projects"))
HTML = """<!doctype html>
<html lang=\"zh-Hant\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>Project Forge AI</title>
    <style>
      body { max-width: 52rem; margin: 4rem auto; padding: 0 1.5rem; font: 18px/1.6 system-ui; background: #10141c; color: #edf2f7; }
      code { color: #63b3ed; } .ok { color: #68d391; }
    </style>
  </head>
  <body>
    <h1>Project Forge AI</h1>
    <p class=\"ok\">Studio foundation is running.</p>
    <p>API health: <code>/api/health</code></p>
    <p>Capabilities: <code>/api/capabilities</code></p>
  </body>
</html>"""


def health() -> dict[str, str]:
    return {"status": "ok", "service": "project-forge-studio", "version": APP_VERSION}


def capabilities() -> dict[str, Any]:
    return {
        "projects_root": str(PROJECTS_ROOT),
        "projects_root_available": PROJECTS_ROOT.is_dir(),
        "features": {
            "model_router": "planned",
            "github": "planned",
            "game_preview": "planned",
            "automation": "planned",
            "agent_tasks": "planned",
        },
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        routes = {
            "/api/health": health,
            "/api/capabilities": capabilities,
        }
        if self.path in routes:
            self._respond_json(routes[self.path]())
        elif self.path in {"/", "/docs"}:
            self._respond(HTTPStatus.OK, "text/html; charset=utf-8", HTML.encode())
        else:
            self._respond_json({"detail": "Not Found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, message_format: str, *args: object) -> None:
        print(f"{self.address_string()} - {message_format % args}", flush=True)

    def _respond_json(self, body: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._respond(status, "application/json", json.dumps(body).encode())

    def _respond(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    print("Project Forge Studio listening on http://0.0.0.0:8080", flush=True)
    server.serve_forever()
