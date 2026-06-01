"""HTML metadata extraction without third-party parser dependencies."""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin

from .models import FetchResult, PageMetadata

WHITESPACE_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]*")


class MetadataExtractor:
    def extract(self, fetch: FetchResult) -> PageMetadata:
        encoding = _encoding_from_content_type(fetch.content_type) or "utf-8"
        document = fetch.body.decode(encoding, errors="replace")
        parser = _MetadataParser(fetch.final_url)
        parser.feed(document)
        parser.close()

        body_text = _clean_text(" ".join(parser.body_parts))
        headings = [_clean_text(value) for value in parser.headings if _clean_text(value)]
        h1 = [_clean_text(value) for value in parser.h1 if _clean_text(value)]
        description = parser.meta.get("description", "")
        keywords = _split_keywords(parser.meta.get("keywords", ""))

        return PageMetadata(
            url=fetch.url,
            final_url=fetch.final_url,
            status_code=fetch.status_code,
            content_type=fetch.content_type,
            title=_clean_text(parser.title),
            description=_clean_text(description),
            keywords=keywords,
            canonical_url=parser.canonical_url,
            language=parser.language,
            h1=h1,
            headings=headings,
            body_text=body_text,
            word_count=len(WORD_RE.findall(body_text)),
            meta=parser.meta,
            open_graph={key[3:]: value for key, value in parser.meta.items() if key.startswith("og:")},
            twitter={key[8:]: value for key, value in parser.meta.items() if key.startswith("twitter:")},
            json_ld=parser.json_ld,
            content_hash=hashlib.sha256(fetch.body).hexdigest(),
            crawl_ms=fetch.crawl_ms,
        )


class _MetadataParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.meta: dict[str, str] = {}
        self.canonical_url = ""
        self.language = ""
        self.h1: list[str] = []
        self.headings: list[str] = []
        self.body_parts: list[str] = []
        self.json_ld: list[dict[str, Any]] = []
        self._tag_stack: list[str] = []
        self._capture_title = False
        self._capture_json_ld = False
        self._json_ld_parts: list[str] = []
        self._heading_tag = ""
        self._heading_parts: list[str] = []
        self._h1_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()
        self._tag_stack.append(tag)

        if tag == "html":
            self.language = attrs_dict.get("lang", self.language)
        elif tag == "title":
            self._capture_title = True
        elif tag == "meta":
            self._handle_meta(attrs_dict)
        elif tag == "link" and attrs_dict.get("rel", "").lower() == "canonical":
            href = attrs_dict.get("href", "")
            self.canonical_url = urljoin(self.base_url, href) if href else ""
        elif tag == "script" and "application/ld+json" in attrs_dict.get("type", ""):
            self._capture_json_ld = True
            self._json_ld_parts = []
        elif tag in {"script", "style", "template", "svg"}:
            self._skip_depth += 1
        elif tag in {"h1", "h2", "h3"}:
            self._heading_tag = tag
            self._heading_parts = []
            if tag == "h1":
                self._h1_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._capture_title = False
        elif tag == "script" and self._capture_json_ld:
            self._store_json_ld()
            self._capture_json_ld = False
            self._json_ld_parts = []
        elif tag in {"script", "style", "template", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag == self._heading_tag:
            heading = _clean_text(" ".join(self._heading_parts))
            if heading:
                self.headings.append(heading)
            if tag == "h1":
                h1 = _clean_text(" ".join(self._h1_parts))
                if h1:
                    self.h1.append(h1)
            self._heading_tag = ""
            self._heading_parts = []
            self._h1_parts = []

        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._capture_json_ld:
            self._json_ld_parts.append(data)
            return
        if self._skip_depth:
            return
        text = html.unescape(data)
        if self._capture_title:
            self.title += " " + text
        if self._heading_tag:
            self._heading_parts.append(text)
            if self._heading_tag == "h1":
                self._h1_parts.append(text)
        if self._is_visible_body_text():
            self.body_parts.append(text)

    def _handle_meta(self, attrs: dict[str, str]) -> None:
        key = attrs.get("name") or attrs.get("property")
        content = attrs.get("content", "")
        if key and content:
            normalized = key.lower()
            self.meta[normalized] = _clean_text(content)
            if normalized == "og:description" and "description" not in self.meta:
                self.meta["description"] = _clean_text(content)
            elif normalized == "og:title" and not self.title:
                self.title = _clean_text(content)

    def _is_visible_body_text(self) -> bool:
        if not self._tag_stack:
            return False
        return self._tag_stack[-1] not in {
            "head",
            "title",
            "meta",
            "link",
            "script",
            "style",
            "template",
            "svg",
        }

    def _store_json_ld(self) -> None:
        raw_json = " ".join(self._json_ld_parts).strip()
        if not raw_json:
            return
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            return
        if isinstance(parsed, dict):
            self.json_ld.append(parsed)
        elif isinstance(parsed, list):
            self.json_ld.extend(item for item in parsed if isinstance(item, dict))


def _encoding_from_content_type(content_type: str) -> str:
    for part in content_type.split(";"):
        key, _, value = part.strip().partition("=")
        if key.lower() == "charset" and value:
            return value.strip()
    return ""


def _clean_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def _split_keywords(value: str) -> list[str]:
    seen: set[str] = set()
    keywords: list[str] = []
    for item in value.split(","):
        cleaned = _clean_text(item).lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            keywords.append(cleaned)
    return keywords


@dataclass(frozen=True)
class ExtractedMetadata:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str
    title: str = ""
    description: str = ""
    canonical_url: str = ""
    language: str = ""
    headings: dict[str, list[str]] = field(default_factory=dict)
    body_text: str = ""
    word_count: int = 0
    meta: dict[str, str] = field(default_factory=dict)
    json_ld: list[dict[str, Any]] = field(default_factory=list)
    content_hash: str = ""
    crawl_ms: int = 0


def extract_metadata(
    requested_url: str,
    final_url: str,
    status_code: int,
    content_type: str,
    body: bytes,
    crawl_ms: int = 0,
) -> ExtractedMetadata:
    """Functional adapter used by assessment tests and simple scripts."""

    fetch = FetchResult(
        url=requested_url,
        final_url=final_url,
        status_code=status_code,
        content_type=content_type,
        body=body,
        crawl_ms=crawl_ms,
    )
    metadata = MetadataExtractor().extract(fetch)
    return ExtractedMetadata(
        requested_url=metadata.url,
        final_url=metadata.final_url,
        status_code=metadata.status_code,
        content_type=metadata.content_type,
        title=metadata.title,
        description=metadata.description,
        canonical_url=metadata.canonical_url,
        language=metadata.language,
        headings={"h1": metadata.h1, "all": metadata.headings},
        body_text=metadata.body_text,
        word_count=metadata.word_count,
        meta=metadata.meta,
        json_ld=metadata.json_ld,
        content_hash=metadata.content_hash,
        crawl_ms=crawl_ms,
    )
