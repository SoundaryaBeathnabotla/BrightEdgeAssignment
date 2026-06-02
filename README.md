# BrightEdge Engineering Assessment: Scale Crawler

This submission includes a runnable URL metadata crawler, topic classifier, local HTTP API, batch file runner, tests, and production design documentation for billion-URL operation.

## Project Contents

| Path | Purpose |
| --- | --- |
| `app/` | Crawler implementation, metadata extraction, classifier, API, CLI, and batch runner. |
| `tests/` | Standard-library unit tests for extraction, classification, API schema, and safety checks. |
| `docs/architecture.md` | Billion-URL production architecture, SLOs, monitoring, cost/reliability design. |
| `docs/schema.md` | Unified metadata schema, storage model, partitioning, retention, idempotency. |
| `docs/poc_release_plan.md` | Proof-of-concept plan, blockers, estimates, release quality gates. |
| `docs/presentation.md` | Short talk track for explaining the solution in an interview/review. |
| `docs/aws_deployment.md` | Step-by-step deployment guide, mostly AWS. |
| `samples/urls_july_2026.txt` | Sample monthly URL input file. |

## What It Does

- Fetches an HTTP/HTTPS URL with timeout, redirect, compression, and response-size safeguards.
- Extracts SEO metadata: title, description, canonical URL, language, headings, OpenGraph, Twitter cards, JSON-LD, body text, word count, and content hash.
- Classifies page type such as `ecommerce`, `news`, `outdoors`, `technical_documentation`, or `generic`.
- Returns relevant topics and confidence scores from a transparent heuristic classifier.
- Supports single-URL CLI, local API demo, and text-file batch processing.
- Handles blocked sites cleanly with structured errors such as `blocked_by_origin`.

## Advanced Backend Features

- SSRF protection blocks private, loopback, link-local, multicast, reserved, and credentialed URLs.
- Robots.txt checks report `robots_disallowed` when a site policy blocks crawling.
- Per-host polite throttling reduces repeated hits to the same domain.
- Structured errors distinguish timeout, DNS failure, origin blocking, robots policy, unsafe URL, and oversized response.
- In-process operational metrics are exposed at `/metrics`.
- Readiness and health endpoints are exposed at `/ready` and `/health`.
- API responses include request IDs for traceability.

## Run Locally

Requires Python 3.10+ and no third-party runtime dependencies.

```bash
python -m app.cli "https://www.amazon.com/Cuisinart-CPT-122-Compact-2-Slice-Toaster/dp/B009GQ034C" --pretty
```

Start the local API:

```bash
python -m app.api --host 127.0.0.1 --port 8000
```

Open the clean browser UI:

```text
http://127.0.0.1:8000/
```

Then call from PowerShell:

```bash
curl -Method POST http://127.0.0.1:8000/crawl -ContentType "application/json" -Body '{"url":"https://www.cnn.com/2025/09/23/tech/google-study-90-percent-tech-jobs-ai","include_body_text":false}'
```

Or open this browser-friendly URL:

```text
http://127.0.0.1:8000/crawl?url=https%3A%2F%2Fexample.com
```

Operational endpoints:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/ready
http://127.0.0.1:8000/metrics
```

Run a URL file:

```bash
python -m app.batch samples/urls_july_2026.txt --output crawl_results.jsonl
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Output Shape

The API returns JSON like:

```json
{
  "metadata": {
    "url": "https://example.com/page",
    "final_url": "https://example.com/page",
    "status_code": 200,
    "title": "Example Page",
    "description": "Example description",
    "canonical_url": "https://example.com/page",
    "word_count": 812,
    "content_hash": "..."
  },
  "classification": {
    "page_type": "news",
    "confidence": 0.66,
    "topics": ["example", "page"]
  }
}
```

## Assessment Mapping

| Assignment part | Where covered |
| --- | --- |
| Part 1: core crawler | `app/fetcher.py`, `app/extractor.py`, `app/classifier.py`, `app/cli.py`, `app/api.py` |
| Part 1: metadata output | `app/models.py`, tests, README output shape |
| Part 1: URL file input | `app/batch.py`, `samples/urls_july_2026.txt` |
| Part 2: billion URL design | `docs/architecture.md` |
| Part 2: unified schema/storage | `docs/schema.md` |
| Part 2: SLO/SLA/monitoring | `docs/architecture.md` |
| Part 3: POC/release plan | `docs/poc_release_plan.md` |
| AI assistance disclosure | `docs/poc_release_plan.md` |

## Production Next Steps

The local crawler should be containerized as a stateless worker. Monthly URL files or MySQL exports feed a dedupe/normalization job, then domain-sharded queues. Worker fleets crawl respectfully using robots/rate-limit controls, write immutable crawl events to object storage, and materialize low-latency metadata indexes for API reads.

See `docs/architecture.md`, `docs/schema.md`, and `docs/poc_release_plan.md` for the detailed operational design.

## Deployment

The AWS deployment path used for this project is Elastic Beanstalk with Docker. A `Dockerfile`, `Procfile`, and Elastic Beanstalk deployment guide are included. See `docs/aws_deployment.md` for exact steps.

Public deployment URL:

```text
http://brightedge-crawler-prod.eba-pejbg5r3.us-east-1.elasticbeanstalk.com/
```

Public crawler example:

```text
http://brightedge-crawler-prod.eba-pejbg5r3.us-east-1.elasticbeanstalk.com/crawl?url=https%3A%2F%2Fexample.com
```

## AI Assistance Disclosure

AI assistance was used to accelerate drafting, implementation, documentation, and review. Human review remains responsible for final technical decisions, testing, and delivery.
