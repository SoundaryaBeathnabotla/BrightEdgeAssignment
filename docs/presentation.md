# Presentation Talk Track

## 1. What I Built

I built a dependency-light Python crawler service for the BrightEdge scale assignment. It accepts a URL, fetches the page, extracts SEO metadata and visible content, classifies the page, returns relevant topics, and exposes the result through a CLI, batch runner, JSON API, and simple browser UI.

The implementation is intentionally easy to run and inspect. It uses the Python standard library for HTTP, HTML parsing, and serving the local API, so reviewers do not need to install a large framework just to evaluate the core logic.

I also added backend controls that matter for real crawler services: SSRF protection, robots.txt checks, per-host polite throttling, structured crawl errors, request IDs, health/readiness endpoints, and an operational `/metrics` endpoint.

## 2. Assignment Coverage

Part 1 is covered by the runnable crawler:

- `app/fetcher.py` validates and fetches URLs with timeout, size limit, and SSRF protections.
- `app/extractor.py` extracts title, description, canonical URL, language, headings, meta tags, JSON-LD, body text, word count, and content hash.
- `app/classifier.py` classifies page type and topics using transparent heuristics.
- `app/api.py` exposes a local API and clean browser UI.
- `app/batch.py` processes a text file of URLs.
- `app/metrics.py` tracks crawl counts, error counts, page-type counts, and latency percentiles.

Part 2 is covered by the production design documentation:

- `docs/architecture.md` explains how to scale from one URL to billions of monthly URLs.
- `docs/schema.md` defines the unified storage schema and partitioning strategy.

Part 3 is covered by:

- `docs/poc_release_plan.md`, which gives the proof-of-concept plan, blockers, estimates, release gates, and evaluation criteria.

## 3. Local Demo Flow

Start the API:

```bash
python -m app.api --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

Operational endpoints:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/ready
http://127.0.0.1:8000/metrics
```

Demo URLs:

```text
https://example.com
https://www.cnn.com/2025/09/23/tech/google-study-90-percent-tech-jobs-ai
https://www.amazon.com/Cuisinart-CPT-122-Compact-2-Slice-Toaster/dp/B009GQ034C
```

The REI assignment URL may return `403 Forbidden`. That is handled as a structured blocked-site result. In production, this would be governed by robots policy, crawl agreements, domain-specific rules, and backoff behavior.

## 4. Architecture Summary

The local crawler becomes a stateless worker in production. Monthly URL lists or MySQL exports feed an ingestion job. URLs are normalized, deduplicated, partitioned by domain, and sent into domain-aware queues. Crawler workers fetch pages respectfully with robots/rate-limit controls. Parser/classifier workers emit immutable crawl events into object storage and materialized metadata into low-latency indexes.

For AWS:

- S3 stores monthly input, raw events, and body text.
- Glue/EMR/Athena handle batch normalization and analytics.
- SQS or MSK handles URL queues.
- Elastic Beanstalk runs the public demo; ECS/Fargate or Batch would run crawler workers at production scale.
- DynamoDB/OpenSearch/Aurora stores serving metadata depending on query patterns.
- CloudWatch/OpenTelemetry/Prometheus track SLOs and operational health.

## 5. Reliability, Cost, and Scale

The design avoids a naive crawler flood by using domain-aware scheduling. Each domain has politeness/rate-limit controls, retry rules, and circuit breakers. This protects target sites and prevents expensive retry storms.

Cost controls include:

- Compressed object storage for raw events.
- Shorter retention for raw HTML.
- Lean metadata records in serving indexes.
- Spot or elastic compute for batch workers.
- Partitioned lakehouse tables for analytics.

Reliability controls include:

- Idempotent writes by `batch_id + normalized_url_hash`.
- Dead-letter queues for permanent failures.
- Backpressure from downstream storage and parser systems.
- Multi-AZ queues and workers.
- SLO burn-rate alerts.

## 6. Known Limitations

This is a strong proof of concept, not a full web-scale crawler. Known limitations:

- Some sites block automated crawlers with HTTP 403.
- JavaScript-rendered pages are not rendered in this POC.
- The classifier is deterministic and explainable, but production should add supervised ML, embeddings, and labeled evaluation sets.
- Standard-library HTML parsing is acceptable for the assessment, but production should use a hardened HTML5 parser.

## 7. How I Would Explain the Result

The project demonstrates the complete path from a single URL crawler to a production-scale crawler design. The code proves the core extraction/classification behavior, while the architecture documentation explains how to operationalize it for billions of URLs with cost, reliability, performance, monitoring, and release planning in mind.

## 8. AI Assistance Disclosure

AI assistance was used to interpret the assignment, accelerate implementation, draft documentation, and review coverage. Final responsibility for the design choices, tests, and delivery remains with the candidate.
