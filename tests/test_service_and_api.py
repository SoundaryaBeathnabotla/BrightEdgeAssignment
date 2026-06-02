import json
import unittest

from app.api import api_schema
from app.fetcher import FetchError, HttpFetcher
from app.metrics import MetricsCollector
from app.models import CrawlError, FetchResult
from app.service import CrawlerService


class FakeFetcher:
    def fetch(self, url: str) -> FetchResult:
        return FetchResult(
            url=url,
            final_url=url,
            status_code=200,
            content_type="text/html",
            body=b"""
            <html><head><title>Shop Running Shoes</title>
            <meta name="description" content="Order shoes with fast shipping">
            </head><body><h1>Running Shoes</h1>
            <p>Add this product to your cart for free shipping.</p></body></html>
            """,
        )


class FailingFetcher:
    def fetch(self, url: str) -> FetchResult:
        raise FetchError("timeout", "Timed out", retryable=True)


class ServiceAndApiTest(unittest.TestCase):
    def test_service_crawls_with_injected_fetcher(self) -> None:
        response = CrawlerService(fetcher=FakeFetcher()).crawl("https://example.com")

        self.assertEqual(response.metadata.title, "Shop Running Shoes")
        self.assertEqual(response.classification.page_type, "ecommerce")
        self.assertIn("running shoes", response.classification.topics)

    def test_service_returns_structured_error(self) -> None:
        result = CrawlerService(fetcher=FailingFetcher()).crawl_or_error("https://example.com")

        self.assertIsInstance(result, CrawlError)
        self.assertEqual(result.code, "timeout")
        self.assertTrue(result.retryable)

    def test_schema_is_json_serializable(self) -> None:
        encoded = json.dumps(api_schema())

        self.assertIn("crawl_request", encoded)
        self.assertIn("crawl_response", encoded)

    def test_metrics_collector_records_success_and_error(self) -> None:
        collector = MetricsCollector()

        collector.record_success("news", 125)
        collector.record_error("blocked_by_origin")
        snapshot = collector.snapshot()

        self.assertEqual(snapshot["counters"]["crawl_total"], 2)
        self.assertEqual(snapshot["counters"]["crawl_success_total"], 1)
        self.assertEqual(snapshot["counters"]["crawl_error_blocked_by_origin_total"], 1)
        self.assertEqual(snapshot["latency_ms"]["p95"], 125)

    def test_fetcher_rejects_unsafe_urls(self) -> None:
        fetcher = HttpFetcher()

        with self.assertRaises(FetchError) as unsupported:
            fetcher._normalize_url("file:///etc/passwd")
        self.assertEqual(unsupported.exception.code, "unsupported_scheme")

        with self.assertRaises(FetchError) as private_host:
            fetcher._normalize_url("http://127.0.0.1/admin")
        self.assertEqual(private_host.exception.code, "blocked_host")


if __name__ == "__main__":
    unittest.main()
