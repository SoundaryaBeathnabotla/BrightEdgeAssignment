"""Small stdlib HTTP API for the crawler.

Run locally:
    python -m app.api --host 127.0.0.1 --port 8000

Endpoints:
    GET  /health
    GET  /schema
    POST /crawl  {"url": "https://example.com", "include_body_text": false}
"""

from __future__ import annotations

import argparse
from html import escape
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .models import CrawlError
from .service import CrawlerService

MAX_REQUEST_BYTES = 16_384


def api_schema() -> dict[str, Any]:
    return {
        "crawl_request": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "include_body_text": {"type": "boolean", "default": True},
            },
        },
        "crawl_response": {
            "type": "object",
            "properties": {
                "metadata": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "final_url": {"type": "string"},
                        "status_code": {"type": "integer"},
                        "content_type": {"type": "string"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "canonical_url": {"type": "string"},
                        "language": {"type": "string"},
                        "h1": {"type": "array", "items": {"type": "string"}},
                        "headings": {"type": "array", "items": {"type": "string"}},
                        "body_text": {"type": "string"},
                        "word_count": {"type": "integer"},
                        "meta": {"type": "object"},
                        "json_ld": {"type": "array", "items": {"type": "object"}},
                        "content_hash": {"type": "string"},
                        "crawl_ms": {"type": "integer"},
                    },
                },
                "classification": {
                    "type": "object",
                    "properties": {
                        "page_type": {"type": "string"},
                        "confidence": {"type": "number"},
                        "topics": {"type": "array", "items": {"type": "string"}},
                        "signals": {"type": "object"},
                    },
                },
            },
        },
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "retryable": {"type": "boolean"},
            },
        },
    }


class CrawlerRequestHandler(BaseHTTPRequestHandler):
    service = CrawlerService()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._write_html(200, _render_home())
        elif self.path == "/health":
            self._write_json(200, {"status": "ok"})
        elif self.path == "/schema":
            self._write_json(200, api_schema())
        elif parsed.path == "/crawl":
            params = parse_qs(parsed.query)
            url = params.get("url", [""])[0]
            if not url:
                self._write_html(
                    400,
                    _render_home(
                        "Enter a URL first, for example https://example.com",
                    ),
                )
                return
            result = self.service.crawl_or_error(url)
            if isinstance(result, CrawlError):
                status = 503 if result.retryable else 400
                self._write_html(status, _render_error(url, result))
                return
            payload = result.to_dict(include_body_text=False)
            if params.get("format", ["html"])[0] == "json":
                self._write_json(200, payload)
            else:
                self._write_html(200, _render_result(payload))
        else:
            self._write_json(404, {"code": "not_found", "message": "Route not found"})

    def do_POST(self) -> None:
        if self.path != "/crawl":
            self._write_json(404, {"code": "not_found", "message": "Route not found"})
            return

        payload = self._read_json()
        if isinstance(payload, CrawlError):
            self._write_json(400, payload.to_dict())
            return

        url = payload.get("url")
        if not isinstance(url, str):
            self._write_json(
                400,
                CrawlError("invalid_request", "Field 'url' must be a string").to_dict(),
            )
            return

        include_body_text = payload.get("include_body_text", True)
        result = self.service.crawl_or_error(url)
        if isinstance(result, CrawlError):
            status = 503 if result.retryable else 400
            self._write_json(status, result.to_dict())
            return

        self._write_json(
            200,
            result.to_dict(include_body_text=bool(include_body_text)),
        )

    def _read_json(self) -> dict[str, Any] | CrawlError:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return CrawlError("invalid_request", "Invalid Content-Length")
        if size <= 0 or size > MAX_REQUEST_BYTES:
            return CrawlError("invalid_request", "Request body size is invalid")
        try:
            return json.loads(self.rfile.read(size).decode("utf-8"))
        except json.JSONDecodeError:
            return CrawlError("invalid_json", "Request body must be valid JSON")

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_html(self, status: int, markup: str) -> None:
        body = markup.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def _page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #172026;
      background: #f4f7f9;
    }}
    body {{ margin: 0; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 56px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.15; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    p {{ margin: 0; color: #53616b; line-height: 1.5; }}
    form {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      margin: 24px 0;
    }}
    input {{
      min-width: 0;
      padding: 13px 14px;
      border: 1px solid #bac7cf;
      border-radius: 6px;
      font-size: 15px;
      background: white;
    }}
    button {{
      border: 0;
      border-radius: 6px;
      padding: 0 18px;
      font-size: 15px;
      font-weight: 700;
      color: white;
      background: #0b6bcb;
      cursor: pointer;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }}
    .card {{
      background: white;
      border: 1px solid #d9e1e6;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }}
    .wide {{ grid-column: 1 / -1; }}
    .kv {{ display: grid; grid-template-columns: 150px 1fr; gap: 8px 14px; }}
    .label {{ color: #687782; font-size: 13px; }}
    .value {{ overflow-wrap: anywhere; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .chip {{ background: #e8f1fb; color: #0b4f92; border-radius: 999px; padding: 5px 10px; font-size: 13px; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #101820; color: #f5f7fa; padding: 14px; border-radius: 6px; }}
    .error {{ border-color: #f1b8b8; background: #fff7f7; color: #8a1f1f; }}
    @media (max-width: 760px) {{
      form, .grid {{ grid-template-columns: 1fr; }}
      button {{ height: 46px; }}
      .kv {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>{body}</main>
</body>
</html>"""


def _render_home(message: str = "") -> str:
    note = f'<div class="card error">{escape(message)}</div>' if message else ""
    return _page(
        "BrightEdge Crawler Checker",
        f"""
<h1>BrightEdge Crawler Checker</h1>
<p>Paste a URL and the service will show extracted metadata, classification, and topics in a cleaner view.</p>
<form action="/crawl" method="get">
  <input name="url" value="https://example.com" aria-label="URL to crawl">
  <button type="submit">Crawl URL</button>
</form>
{note}
<div class="grid">
  <div class="card">
    <h2>API Health</h2>
    <p>Use <a href="/health">/health</a> to verify the server is running.</p>
  </div>
  <div class="card">
    <h2>JSON Mode</h2>
    <p>Add <code>&format=json</code> to the crawl URL when you want raw JSON.</p>
  </div>
</div>
""",
    )


def _render_result(payload: dict[str, Any]) -> str:
    metadata = payload.get("metadata", {})
    classification = payload.get("classification", {})
    topics = classification.get("topics", [])
    topic_chips = "".join(f'<span class="chip">{escape(str(topic))}</span>' for topic in topics)
    raw_json = escape(json.dumps(payload, indent=2, ensure_ascii=True))
    return _page(
        "Crawl Result",
        f"""
<h1>Crawl Result</h1>
<p>{escape(str(metadata.get("final_url", metadata.get("url", ""))))}</p>
<form action="/crawl" method="get">
  <input name="url" value="{escape(str(metadata.get("url", "")))}" aria-label="URL to crawl">
  <button type="submit">Crawl URL</button>
</form>
<div class="grid">
  <section class="card">
    <h2>Classification</h2>
    <div class="kv">
      <div class="label">Page type</div><div class="value">{escape(str(classification.get("page_type", "")))}</div>
      <div class="label">Confidence</div><div class="value">{escape(str(classification.get("confidence", "")))}</div>
      <div class="label">Crawl time</div><div class="value">{escape(str(metadata.get("crawl_ms", "")))} ms</div>
      <div class="label">Word count</div><div class="value">{escape(str(metadata.get("word_count", "")))}</div>
    </div>
  </section>
  <section class="card">
    <h2>Topics</h2>
    <div class="chips">{topic_chips}</div>
  </section>
  <section class="card wide">
    <h2>Metadata</h2>
    <div class="kv">
      <div class="label">Title</div><div class="value">{escape(str(metadata.get("title", "")))}</div>
      <div class="label">Description</div><div class="value">{escape(str(metadata.get("description", "")))}</div>
      <div class="label">Canonical</div><div class="value">{escape(str(metadata.get("canonical_url", "")))}</div>
      <div class="label">Status</div><div class="value">{escape(str(metadata.get("status_code", "")))}</div>
      <div class="label">Content type</div><div class="value">{escape(str(metadata.get("content_type", "")))}</div>
    </div>
  </section>
  <section class="card wide">
    <h2>Raw JSON</h2>
    <pre>{raw_json}</pre>
  </section>
</div>
""",
    )


def _render_error(url: str, error: CrawlError) -> str:
    return _page(
        "Crawl Error",
        f"""
<h1>Crawl Error</h1>
<form action="/crawl" method="get">
  <input name="url" value="{escape(url)}" aria-label="URL to crawl">
  <button type="submit">Try Again</button>
</form>
<div class="card error">
  <h2>{escape(error.code)}</h2>
  <p>{escape(error.message)}</p>
</div>
""",
    )


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), CrawlerRequestHandler)
    print(f"crawler API listening on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.getenv("PORT", "8000")), type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
