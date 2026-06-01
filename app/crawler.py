from __future__ import annotations

from app.fetcher import HttpFetcher
from app.models import CrawlResponse
from app.service import CrawlerService


def crawl(url: str, timeout_seconds: float = 10.0) -> CrawlResponse:
    return CrawlerService(fetcher=HttpFetcher(timeout_seconds=timeout_seconds)).crawl(url)
