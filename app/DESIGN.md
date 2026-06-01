# BrightEdge Crawler Implementation Design

## Scope

This package implements a dependency-light proof of concept for crawling one URL, extracting HTML metadata, classifying page type, and returning relevant topics through a JSON API. It uses Python standard library components only so it can run in restricted candidate-assessment environments.

## Local API Contract

Run:

```bash
python -m app.api --host 127.0.0.1 --port 8000
```

Endpoints:

- `GET /health` returns service status.
- `GET /schema` returns the request, response, and error schema.
- `POST /crawl` accepts `{"url": "https://example.com", "include_body_text": false}`.

The response contains:

- `metadata`: URL, final URL, status, content type, title, description, keywords, canonical URL, language, H1s, headings, visible body text, word count, and raw meta map.
- `classification`: page type, confidence, ranked topics, and category scoring signals.

## Fetch Design

`app.fetcher.HttpFetcher` uses `urllib.request` with explicit timeout, byte limit, and user agent. It accepts only `http` and `https`, strips fragments, rejects URL credentials, and blocks private, loopback, link-local, multicast, reserved, and unspecified IP targets by default. This reduces SSRF risk for a public crawl API. Production would also enforce DNS rebinding controls, per-tenant rate limits, robots policy, redirect limits, and shared egress allow/block lists.

## Metadata Extraction

`app.extractor.MetadataExtractor` uses `html.parser` to avoid parser dependencies. It extracts title, meta description, meta keywords, Open Graph title/description fallbacks, canonical URL, language, headings, H1s, visible body text, and word count. Scripts, styles, templates, and SVG text are ignored. For production, I would use a hardened HTML5 parser because real-world malformed markup is common.

## Classification and Topics

`app.classifier.TopicClassifier` provides deterministic heuristic classification across categories such as ecommerce, technical documentation, news, jobs, finance, healthcare, education, and travel. Topics are derived from high-signal fields first, then weighted token frequency. This is explainable and stable for a POC. Production should upgrade this to a hybrid of deterministic rules, supervised ML, embeddings, and knowledge-graph/entity extraction with offline evaluation sets.

## Production Architecture for Billions of URLs

A production crawler should be asynchronous and queue-driven:

- URL intake API validates requests, normalizes URLs, deduplicates by canonical URL and content hash, and writes crawl jobs to Kafka/Pub/Sub/SQS.
- Scheduler partitions work by host and crawl priority, enforces robots.txt, crawl-delay, host politeness, recrawl cadence, and customer quota.
- Fetch workers run in isolated egress pools with DNS pinning, redirect controls, adaptive concurrency, and per-host circuit breakers.
- Extraction workers parse HTML, boilerplate-clean content, extract metadata, classify topics, and emit versioned documents.
- Storage separates raw fetch artifacts, extracted metadata, content hashes, link graph edges, and classification outputs. Object storage can hold raw/compressed pages; a document store or columnar table can hold extracted records; a search index supports query/debug workflows.
- Observability and audit streams capture every fetch outcome, normalized URL, final URL, fetch timing, parser version, classifier version, and retry decision.

To scale to billions, partition primarily by registrable domain and normalized URL hash. Keep fetch workers stateless, cache DNS and robots decisions with short TTLs, and use backpressure from downstream extraction/storage systems to the scheduler.

## SLO, SLA, and Monitoring

Suggested SLOs for an internal crawl API:

- API availability: 99.9% monthly for accepted crawl requests.
- API latency: p95 under 300 ms for accepted job creation; synchronous POC crawl latency is network-bound and should not be the production SLA shape.
- Freshness: 95% of priority URLs crawled within configured recrawl interval.
- Success rate: 98% of fetchable public HTML URLs complete extraction within 15 minutes.
- Data quality: 99% of successful HTML fetches produce non-empty title or body text.

Core metrics:

- Request rate, accepted/rejected jobs, queue depth, queue age, worker utilization.
- Fetch latency, DNS latency, response size, status-code distribution, retry rate, timeout rate.
- Per-host concurrency, politeness throttles, robots exclusions, circuit-breaker opens.
- Extraction parse failures, empty body rate, metadata field coverage, classifier distribution drift.
- Storage write latency/errors, duplicate rate, canonicalization changes.

Alert examples:

- Queue age p95 exceeds freshness budget.
- Fetch timeout rate or 5xx rate doubles baseline for 15 minutes.
- Parser error rate exceeds 1% after deployment.
- Classifier output distribution shifts sharply from trailing seven-day baseline.

## POC Blockers and Risks

- Standard-library HTML parsing is acceptable for a POC but weaker on malformed HTML than production parsers.
- Synchronous fetching is simple but unsuitable for high fanout crawling.
- Heuristic classification is explainable but will underperform on ambiguous pages and multilingual content.
- The current POC does not execute JavaScript, so SPA-only content may appear empty.
- Robots.txt handling, host politeness, redirect limits, content-language detection, boilerplate removal, and persistent storage are design items rather than implemented POC features.

## Estimates

- POC hardening: 2-3 engineering days for redirect limits, robots.txt, richer parser tests, and local CLI ergonomics.
- Production MVP: 6-8 weeks with two backend engineers and one data/ML engineer for queueing, scheduler, workers, storage, observability, and rule-based classification.
- Production scale-up: 3-4 additional months for billion-URL operations, robust recrawl scheduling, ML classification, multilingual support, evaluation tooling, and cost controls.

## Release Plan

1. POC: ship local API, tests, and design review.
2. Alpha: add async job queue, persistent storage, robots enforcement, and dashboards for internal users.
3. Beta: onboard limited customer/domain sets, tune politeness, add replayable extraction/classification pipelines, and publish API versioning.
4. GA: add multi-region worker pools, formal SLOs, incident runbooks, cost budgets, and model/rule evaluation gates.
5. Continuous improvement: classifier retraining, parser upgrades, recrawl optimization, and drift monitoring.

## AI Assistance Disclosure

AI assistance was used to draft and implement this POC service structure, tests, and design notes. The approach intentionally favors readable, dependency-light Python and explicit tradeoffs suitable for an engineering assessment.
