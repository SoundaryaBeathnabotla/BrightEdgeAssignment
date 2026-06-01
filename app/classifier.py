"""Transparent heuristic page classification and topic extraction."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .models import PageClassification, PageMetadata

TOKEN_RE = re.compile(r"[a-z][a-z0-9'-]{2,}")

STOPWORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "articles",
    "but",
    "can",
    "contact",
    "for",
    "from",
    "has",
    "have",
    "home",
    "how",
    "into",
    "learn",
    "more",
    "new",
    "news",
    "not",
    "our",
    "page",
    "privacy",
    "read",
    "search",
    "services",
    "site",
    "that",
    "the",
    "their",
    "this",
    "with",
    "you",
    "your",
}

CATEGORY_TERMS: dict[str, set[str]] = {
    "ecommerce": {
        "add",
        "bag",
        "cart",
        "checkout",
        "coupon",
        "delivery",
        "discount",
        "order",
        "price",
        "product",
        "shipping",
        "shop",
        "sku",
    },
    "technical_documentation": {
        "api",
        "cli",
        "configuration",
        "developer",
        "docs",
        "endpoint",
        "example",
        "guide",
        "install",
        "reference",
        "sdk",
        "tutorial",
    },
    "news": {
        "breaking",
        "coverage",
        "daily",
        "editor",
        "headline",
        "journal",
        "latest",
        "media",
        "news",
        "press",
        "report",
        "story",
        "updates",
    },
    "jobs": {
        "apply",
        "benefits",
        "career",
        "hiring",
        "job",
        "position",
        "recruiting",
        "remote",
        "resume",
        "salary",
        "team",
    },
    "finance": {
        "bank",
        "earnings",
        "finance",
        "fund",
        "investment",
        "loan",
        "market",
        "mortgage",
        "portfolio",
        "revenue",
        "stock",
        "trading",
    },
    "healthcare": {
        "care",
        "clinic",
        "doctor",
        "health",
        "hospital",
        "medical",
        "patient",
        "pharmacy",
        "symptoms",
        "treatment",
        "wellness",
    },
    "education": {
        "admission",
        "campus",
        "class",
        "course",
        "curriculum",
        "degree",
        "education",
        "faculty",
        "learning",
        "school",
        "student",
        "university",
    },
    "outdoors": {
        "camp",
        "camping",
        "comfortable",
        "friend",
        "gear",
        "hike",
        "indoorsy",
        "outdoor",
        "outdoors",
        "pack",
        "rei",
        "trail",
    },
    "travel": {
        "booking",
        "destination",
        "flight",
        "hotel",
        "itinerary",
        "resort",
        "tour",
        "travel",
        "trip",
        "vacation",
    },
}


class TopicClassifier:
    def classify(self, metadata: PageMetadata) -> PageClassification:
        weighted_tokens = self._weighted_tokens(metadata)
        category_scores = self._category_scores(weighted_tokens)
        if category_scores:
            page_type, raw_score = max(category_scores.items(), key=lambda item: item[1])
            confidence = min(0.98, round(raw_score / (raw_score + 6.0), 2))
        else:
            page_type = "generic"
            raw_score = 0.0
            confidence = 0.35

        topics = self._topics(metadata, weighted_tokens, page_type)
        return PageClassification(
            page_type=page_type,
            confidence=confidence,
            topics=topics,
            signals={key: round(value, 2) for key, value in sorted(category_scores.items())},
        )

    def _weighted_tokens(self, metadata: PageMetadata) -> Counter[str]:
        tokens: Counter[str] = Counter()
        fields = [
            (metadata.title, 5),
            (metadata.description, 4),
            (" ".join(metadata.keywords), 5),
            (" ".join(metadata.h1), 4),
            (" ".join(metadata.headings), 2),
            (metadata.body_text, 1),
        ]
        for text, weight in fields:
            for token in _tokens(text):
                tokens[token] += weight
        return tokens

    def _category_scores(self, tokens: Counter[str]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for category, terms in CATEGORY_TERMS.items():
            score = 0.0
            for term in terms:
                if term in tokens:
                    score += 1.0 + math.log(tokens[term] + 1, 2)
            if score:
                scores[category] = score
        return scores

    def _topics(
        self,
        metadata: PageMetadata,
        tokens: Counter[str],
        page_type: str,
        max_topics: int = 10,
    ) -> list[str]:
        topics: list[str] = []
        seen: set[str] = set()

        for source in [metadata.keywords, metadata.h1, [metadata.title]]:
            for phrase in source:
                normalized = _topic_phrase(phrase)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    topics.append(normalized)
                if len(topics) >= max_topics:
                    return topics

        for token, _count in tokens.most_common(40):
            if token in STOPWORDS or token in seen:
                continue
            seen.add(token)
            topics.append(token)
            if len(topics) >= max_topics:
                break

        if not topics and page_type != "generic":
            topics.append(page_type.replace("_", " "))
        return topics


@dataclass(frozen=True)
class ClassifiedTopic:
    topic: str
    score: float


@dataclass(frozen=True)
class ClassificationResult:
    page_type: str
    confidence: float
    topics: list[dict[str, float | str]] = field(default_factory=list)
    signals: dict[str, float] = field(default_factory=dict)


def classify_page(metadata: Any) -> ClassificationResult:
    """Functional adapter with product/article naming for assessment callers."""

    text = _metadata_text(metadata)
    meta = getattr(metadata, "meta", {}) or {}
    og_type = str(meta.get("og:type", "")).lower()

    base_metadata = PageMetadata(
        url=getattr(metadata, "requested_url", getattr(metadata, "url", "")),
        final_url=getattr(metadata, "final_url", ""),
        status_code=getattr(metadata, "status_code", 0),
        content_type=getattr(metadata, "content_type", ""),
        title=getattr(metadata, "title", ""),
        description=getattr(metadata, "description", ""),
        h1=(getattr(metadata, "headings", {}) or {}).get("h1", []),
        headings=(getattr(metadata, "headings", {}) or {}).get("all", []),
        body_text=getattr(metadata, "body_text", ""),
        meta=meta,
    )
    heuristic = TopicClassifier().classify(base_metadata)

    if og_type == "product" or heuristic.page_type == "ecommerce":
        page_type = "product"
        confidence = max(0.82, heuristic.confidence)
    elif og_type == "article" or _contains_any(text, {"article", "blog", "story", "advice"}):
        page_type = "article"
        confidence = max(0.75, heuristic.confidence)
    else:
        page_type = heuristic.page_type
        confidence = heuristic.confidence

    topics = _assessment_topics(text, heuristic.topics)
    return ClassificationResult(
        page_type=page_type,
        confidence=confidence,
        topics=[{"topic": topic.topic, "score": topic.score} for topic in topics],
        signals=heuristic.signals,
    )


def _metadata_text(metadata: Any) -> str:
    headings = getattr(metadata, "headings", {}) or {}
    heading_text = " ".join(value for values in headings.values() for value in values)
    fields = [
        getattr(metadata, "title", ""),
        getattr(metadata, "description", ""),
        heading_text,
        getattr(metadata, "body_text", ""),
    ]
    return " ".join(fields).lower()


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _assessment_topics(text: str, fallback_topics: list[str]) -> list[ClassifiedTopic]:
    rules = [
        ("outdoors", {"camp", "camping", "outdoor", "outdoors", "trail", "gear"}, 3.0),
        ("commerce", {"cart", "order", "price", "product", "reviews", "shipping", "shop"}, 2.5),
        ("kitchen", {"appliance", "bread", "counter", "kitchen", "toaster"}, 2.0),
        ("developer", {"api", "cli", "developer", "docs", "endpoint", "sdk"}, 2.0),
        ("seo", {"content", "keyword", "ranking", "seo", "topic"}, 2.0),
        ("careers", {"apply", "career", "hiring", "job", "salary"}, 2.0),
    ]
    scored: list[ClassifiedTopic] = []
    for topic, terms, weight in rules:
        hits = sum(1 for term in terms if term in text)
        if hits:
            scored.append(ClassifiedTopic(topic=topic, score=round(hits * weight, 2)))

    existing = {item.topic for item in scored}
    for topic in fallback_topics:
        if topic not in existing:
            scored.append(ClassifiedTopic(topic=topic, score=1.0))
            existing.add(topic)

    return sorted(scored, key=lambda item: item.score, reverse=True)[:10]


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS and not token.isdigit()
    ]


def _topic_phrase(text: str) -> str:
    normalized = " ".join(_tokens(text))
    if len(normalized) < 3:
        return ""
    return normalized[:80]
