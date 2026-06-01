# Proof of Concept Evaluation and Release Plan

## POC Objective

The proof of concept should demonstrate that the crawler can accept URL inputs, fetch crawlable pages, extract useful SEO metadata, classify pages into high-level page types, generate relevant topics, and emit records that match `docs/schema.md`. The POC should also show a credible path from a small local run to a distributed pipeline capable of handling BrightEdge-scale crawl volumes.

## Engineering Path to POC

1. Confirm assignment coverage.
   - Map each assignment requirement to a runnable feature, test, or documented limitation.
   - Use the three assignment URLs as the minimum reviewer-facing demo set.

2. Stabilize the local crawler workflow.
   - Validate and normalize URLs before crawl.
   - Fetch HTML with timeout, retry, and clear failure classification.
   - Extract title, description, canonical URL, body text, status code, and fetch metadata.
   - Emit JSON records that follow the documented schema.

3. Add classification and topic generation.
   - Classify pages into product, article, or general webpage categories.
   - Generate top topics from page text and metadata.
   - Keep confidence scores or review notes where the model/heuristic is uncertain.

4. Prove operational behavior.
   - Handle malformed URLs, non-HTML responses, blocked pages, redirects, and transient network failures.
   - Ensure failed URLs are recorded, not silently dropped.
   - Produce a small accuracy report from manual sampling.

5. Prepare scale-up evidence.
   - Run a 1,000 URL mixed-domain sample.
   - Run or simulate a 100,000 URL stress sample.
   - Extrapolate throughput, storage, queue, and cost estimates to one billion URLs.

## POC Inputs and Outputs

POC inputs:

- The three assignment URLs.
- A 1,000 URL mixed-domain validation sample.
- A 100,000 URL stress sample from stored monthly input or a synthetic domain distribution.

POC outputs:

- JSON metadata records matching `docs/schema.md`.
- Crawl summary with success, retry, redirect, blocked, parse-error, and permanent-failure counts.
- Accuracy report from sampled manual review.
- Throughput and cost model extrapolated to one billion URLs.
- Operational notes for retries, blocked domains, failed parses, and queue backlog.

## Evaluation Criteria

| Criterion | Target |
| --- | --- |
| URL validation | Rejects malformed and non-http(s) URLs deterministically. |
| Metadata extraction | Extracts title, description, canonical URL, and body text on at least 95% of sampled crawlable HTML pages where those fields exist. |
| Page classification | Correctly identifies product vs article vs webpage on at least 90% of a labeled sample. |
| Topic quality | Top 5 topics are judged relevant on at least 85% of sampled pages. |
| Schema compliance | 100% of successful output records validate against `docs/schema.md`. |
| Resilience | Retries transient failures, records permanent failures, and never drops a URL silently. |
| Performance | Single-worker parsing completes in under 500 ms for typical small HTML pages, excluding network time. |

## Timeline and Implementation Schedule

| Phase | ETA | Deliverables |
| --- | ---: | --- |
| POC scope lock | 0.5 day | Requirement map, demo URL set, evaluation checklist. |
| Local crawler completion | 1-2 days | URL validation, fetch, parse, JSON output, deterministic local run. |
| Classification and topics | 1 day | Page-type classifier, topic extraction, confidence/review notes. |
| Reliability pass | 1 day | Retry policy, timeout handling, failure records, redirect/non-HTML handling. |
| Test and quality pass | 1 day | Unit tests, integration/smoke test, schema validation, lint/build pass. |
| Scale evidence | 1-2 days | 1,000 URL sample, 100,000 URL stress/simulation, cost and throughput model. |
| Release prep | 0.5-1 day | Demo instructions, known limitations, AI disclosure, final review notes. |

Estimated POC ETA: 6-8 engineering days from a working implementation branch. If the crawler and schema are already implemented, the remaining assessment-ready release pass should take about 2-3 days.

## Known Work, Trivial Items, and Blockers

Trivial or well-bounded items:

- URL syntax validation and normalization.
- HTML metadata parsing for common tags.
- JSON output contract validation.
- Local CLI or API demo flow.
- Basic product/article/webpage classification.
- Summary reporting for crawl outcomes.

Known harder items:

- Domain politeness and throttling at high throughput.
- Handling bot protection, CAPTCHAs, and JavaScript-rendered pages.
- Maintaining topic quality across industries, templates, and languages.
- Preventing large domains from starving long-tail domains.
- Defining retention policies for raw HTML and extracted body text.

Potential blockers:

- Legal or compliance constraints around crawling, robots.txt, and data retention.
- Cloud quota limits for queue throughput, NAT bandwidth, storage writes, or index writes.
- Pages that require JavaScript rendering or block automated clients.
- Insufficient labeled data for measuring topic relevance and classification accuracy.
- Ambiguous ownership of customer-facing SLA versus internal SLO targets.

## Release Quality Gates

Before a high-quality release candidate:

- Unit, integration, and smoke tests pass in CI or documented local verification.
- Output records validate against `docs/schema.md`.
- Sample crawl report is reviewed against labeled expected results.
- The demo URLs run successfully from a clean checkout using documented commands.
- Load or stress results support the throughput and cost model.
- Observability plan covers success rate, failure categories, parser errors, queue backlog, crawl latency, and cost.
- Runbook covers retry storms, domain blocking, parser regressions, queue backlog, failed deployments, and rollback.
- Security review approves dependency list, network egress policy, storage access controls, and secret handling.
- Known limitations are documented with severity and recommended next action.

## Demo Instructions

The final README or submission notes should include exact commands once the implementation branch is available.

1. Install dependencies.

   ```bash
   <package-manager> install
   ```

2. Configure environment.

   ```bash
   cp <example-env-file> <local-env-file>
   ```

3. Run the three assignment URLs.

   ```bash
   <package-manager> run crawl -- <assignment-url-file>
   ```

4. Validate output.

   ```bash
   <package-manager> run validate-output
   ```

5. Run verification.

   ```bash
   <package-manager> test
   <package-manager> run lint
   <package-manager> run build
   ```

Expected demo result: the reviewer can run the crawler, inspect generated JSON records, confirm schema compliance, and see a summary of successful, retried, blocked, and failed URLs.

## POC Evaluation Documentation

Include the following artifacts with the assessment submission:

- Requirement traceability checklist.
- Demo command list and expected output location.
- Sample crawl report for the three assignment URLs.
- Accuracy review table for a labeled sample.
- 1,000 URL validation summary.
- 100,000 URL stress or simulation summary.
- Throughput, storage, and cost assumptions for one billion URLs.
- Known limitations and production follow-up list.

## AI Assistance Disclosure

Suggested submission wording:

> I used AI coding assistance as a drafting and review aid during this assessment. It helped organize the proof-of-concept release plan, identify risks and quality gates, refine evaluation criteria, and draft reviewer-facing documentation. I remained responsible for final technical decisions, validation, and submitted content. No proprietary secrets or credentials were provided to the AI tool.

AI tools used:

- OpenAI Codex: Helped structure this POC evaluation and release plan, summarize risks and blockers, define quality gates, and draft AI assistance disclosure wording.

Reviewer note:

> AI assistance was used for planning and documentation support, not as a substitute for engineering judgment. Implementation behavior, tests, and release readiness should be evaluated against the repository contents and documented demo results.
