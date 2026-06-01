from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.crawler import crawl


class CrawlerHandler(BaseHTTPRequestHandler):
    server_version = "BrightEdgeCrawlerDemo/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok"})
            return
        if parsed.path != "/crawl":
            self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
            return
        params = parse_qs(parsed.query)
        url = params.get("url", [""])[0]
        if not url:
            self._send_json({"error": "missing required query parameter: url"}, status=HTTPStatus.BAD_REQUEST)
            return
        try:
            result = crawl(url).to_dict()
        except Exception as exc:
            self._send_json({"url": url, "error": str(exc)}, status=HTTPStatus.BAD_GATEWAY)
            return
        self._send_json(result)

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8080), CrawlerHandler)
    print("Serving BrightEdge crawler demo at http://127.0.0.1:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()
