"""HTTP fetching with conservative safety defaults."""

from __future__ import annotations

import ipaddress
import socket
import time
from urllib.error import HTTPError
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urldefrag, urlparse
from urllib.request import Request, urlopen

from .models import FetchResult


class FetchError(Exception):
    """Raised when a URL cannot be fetched safely or successfully."""

    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class HttpFetcher:
    timeout_seconds: float = 8.0
    max_bytes: int = 10_000_000
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36 "
        "BrightEdgeAssessmentCrawler/1.0"
    )
    allow_private_hosts: bool = False

    def fetch(self, url: str) -> FetchResult:
        normalized = self._normalize_url(url)
        request = Request(
            normalized,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            method="GET",
        )

        started = time.perf_counter()
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read(self.max_bytes + 1)
                if len(body) > self.max_bytes:
                    raise FetchError(
                        "response_too_large",
                        f"Response exceeds configured limit of {self.max_bytes} bytes",
                    )
                return FetchResult(
                    url=normalized,
                    final_url=response.geturl(),
                    status_code=response.status,
                    content_type=response.headers.get("Content-Type", ""),
                    body=body,
                    crawl_ms=int((time.perf_counter() - started) * 1000),
                )
        except FetchError:
            raise
        except HTTPError as exc:
            if exc.code == 403:
                raise FetchError(
                    "blocked_by_origin",
                    "The target site returned HTTP 403 Forbidden. This usually means it blocks automated crawlers.",
                    retryable=False,
                ) from exc
            raise FetchError("http_error", f"HTTP Error {exc.code}: {exc.reason}", retryable=500 <= exc.code < 600) from exc
        except TimeoutError as exc:
            raise FetchError("timeout", "Timed out fetching URL", retryable=True) from exc
        except Exception as exc:  # urllib raises several protocol-specific exceptions.
            raise FetchError("fetch_failed", str(exc), retryable=True) from exc

    def _normalize_url(self, raw_url: str) -> str:
        if not raw_url or not raw_url.strip():
            raise FetchError("invalid_url", "URL is required")

        url, _fragment = urldefrag(raw_url.strip())
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise FetchError("unsupported_scheme", "Only http and https URLs are supported")
        if not parsed.hostname:
            raise FetchError("invalid_url", "URL must include a host")
        if parsed.username or parsed.password:
            raise FetchError("invalid_url", "Credentials in URLs are not supported")

        if not self.allow_private_hosts:
            self._reject_private_host(parsed.hostname)
        return url

    def _reject_private_host(self, host: str) -> None:
        try:
            addresses = self._resolve_host(host)
        except socket.gaierror as exc:
            raise FetchError("dns_failed", f"Could not resolve host {host}", retryable=True) from exc

        for address in addresses:
            ip = ipaddress.ip_address(address)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                raise FetchError("blocked_host", "Private and non-routable hosts are blocked")

    @staticmethod
    def _resolve_host(host: str) -> Iterable[str]:
        return {
            result[4][0]
            for result in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        }
