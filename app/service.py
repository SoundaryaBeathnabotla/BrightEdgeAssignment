"""Crawler orchestration service."""

from __future__ import annotations

from .classifier import TopicClassifier
from .extractor import MetadataExtractor
from .fetcher import FetchError, HttpFetcher
from .models import CrawlError, CrawlResponse


class CrawlerService:
    def __init__(
        self,
        fetcher: HttpFetcher | None = None,
        extractor: MetadataExtractor | None = None,
        classifier: TopicClassifier | None = None,
    ) -> None:
        self.fetcher = fetcher or HttpFetcher()
        self.extractor = extractor or MetadataExtractor()
        self.classifier = classifier or TopicClassifier()

    def crawl(self, url: str) -> CrawlResponse:
        fetch = self.fetcher.fetch(url)
        metadata = self.extractor.extract(fetch)
        classification = self.classifier.classify(metadata)
        return CrawlResponse(metadata=metadata, classification=classification)

    def crawl_or_error(self, url: str) -> CrawlResponse | CrawlError:
        try:
            return self.crawl(url)
        except FetchError as exc:
            return CrawlError(code=exc.code, message=str(exc), retryable=exc.retryable)
