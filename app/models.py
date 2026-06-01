"""Data contracts for the crawler service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    body: bytes
    crawl_ms: int = 0


@dataclass(frozen=True)
class PageMetadata:
    url: str
    final_url: str
    status_code: int
    content_type: str
    title: str = ""
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    canonical_url: str = ""
    language: str = ""
    h1: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    body_text: str = ""
    word_count: int = 0
    meta: dict[str, str] = field(default_factory=dict)
    open_graph: dict[str, str] = field(default_factory=dict)
    twitter: dict[str, str] = field(default_factory=dict)
    json_ld: list[dict[str, Any]] = field(default_factory=list)
    content_hash: str = ""
    crawl_ms: int = 0


@dataclass(frozen=True)
class PageClassification:
    page_type: str
    confidence: float
    topics: list[str]
    signals: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class CrawlResponse:
    metadata: PageMetadata
    classification: PageClassification

    def to_dict(self, include_body_text: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        if not include_body_text:
            payload["metadata"].pop("body_text", None)
        return payload


@dataclass(frozen=True)
class CrawlError:
    code: str
    message: str
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
