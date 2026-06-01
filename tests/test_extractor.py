import unittest

from app.extractor import MetadataExtractor
from app.models import FetchResult


class MetadataExtractorTest(unittest.TestCase):
    def test_extracts_core_metadata_and_visible_text(self) -> None:
        html = b"""
        <html lang="en">
          <head>
            <title>  BrightEdge SEO Platform </title>
            <meta name="description" content="Enterprise SEO insights and reporting">
            <meta name="keywords" content="SEO, content marketing, SEO">
            <link rel="canonical" href="/platform">
            <style>.hidden { display: none }</style>
          </head>
          <body>
            <h1>SEO Platform</h1>
            <h2>Content Recommendations</h2>
            <script>console.log("ignore me")</script>
            <p>Analyze pages, topics, and competitors.</p>
          </body>
        </html>
        """
        fetch = FetchResult(
            url="https://example.com",
            final_url="https://example.com/index.html",
            status_code=200,
            content_type="text/html; charset=utf-8",
            body=html,
        )

        metadata = MetadataExtractor().extract(fetch)

        self.assertEqual(metadata.title, "BrightEdge SEO Platform")
        self.assertEqual(metadata.description, "Enterprise SEO insights and reporting")
        self.assertEqual(metadata.keywords, ["seo", "content marketing"])
        self.assertEqual(metadata.canonical_url, "https://example.com/platform")
        self.assertEqual(metadata.language, "en")
        self.assertEqual(metadata.h1, ["SEO Platform"])
        self.assertIn("Content Recommendations", metadata.headings)
        self.assertIn("Analyze pages", metadata.body_text)
        self.assertNotIn("console.log", metadata.body_text)
        self.assertGreater(metadata.word_count, 5)


if __name__ == "__main__":
    unittest.main()
