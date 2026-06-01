import unittest

from app.classifier import TopicClassifier
from app.models import PageMetadata


class TopicClassifierTest(unittest.TestCase):
    def test_classifies_technical_documentation(self) -> None:
        metadata = PageMetadata(
            url="https://example.com/docs/api",
            final_url="https://example.com/docs/api",
            status_code=200,
            content_type="text/html",
            title="API Reference Guide",
            description="Developer docs with endpoint examples and SDK install steps.",
            keywords=["api", "sdk", "developer docs"],
            h1=["API Reference"],
            headings=["Authentication", "Endpoint examples"],
            body_text="Install the CLI and configure each API endpoint with examples.",
        )

        classification = TopicClassifier().classify(metadata)

        self.assertEqual(classification.page_type, "technical_documentation")
        self.assertGreaterEqual(classification.confidence, 0.7)
        self.assertIn("api", classification.topics)
        self.assertIn("technical_documentation", classification.signals)

    def test_returns_generic_for_low_signal_page(self) -> None:
        metadata = PageMetadata(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            content_type="text/html",
            title="Welcome",
            body_text="A short welcome page.",
        )

        classification = TopicClassifier().classify(metadata)

        self.assertEqual(classification.page_type, "generic")
        self.assertLessEqual(classification.confidence, 0.4)


if __name__ == "__main__":
    unittest.main()
