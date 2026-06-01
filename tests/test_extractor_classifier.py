import unittest

from app.classifier import TopicClassifier
from app.extractor import extract_metadata
from app.models import PageMetadata


PRODUCT_HTML = b"""
<!doctype html>
<html lang="en">
  <head>
    <title>Cuisinart CPT-122 Compact 2-Slice Toaster</title>
    <meta name="description" content="Compact toaster for kitchen counters with shade settings.">
    <meta property="og:type" content="product">
    <meta property="og:title" content="Cuisinart Toaster">
    <link rel="canonical" href="https://www.amazon.com/dp/B009GQ034C">
    <script type="application/ld+json">{"@type":"Product","name":"Cuisinart Toaster"}</script>
  </head>
  <body>
    <h1>Cuisinart compact toaster</h1>
    <p>This kitchen appliance toasts bread and has product reviews, price, and shipping.</p>
  </body>
</html>
"""


ARTICLE_HTML = b"""
<html>
  <head>
    <title>How to introduce your indoorsy friend to the outdoors</title>
    <meta name="description" content="REI camping advice for getting a friend outdoors.">
    <meta property="og:type" content="article">
  </head>
  <body>
    <h1>Camping with a friend</h1>
    <p>Choose a short trail, pack outdoor gear, and make the first camp trip comfortable.</p>
  </body>
</html>
"""


class ExtractorClassifierTests(unittest.TestCase):
    def test_extracts_core_metadata_and_json_ld(self) -> None:
        metadata = extract_metadata(
            requested_url="https://www.amazon.com/dp/B009GQ034C",
            final_url="https://www.amazon.com/dp/B009GQ034C",
            status_code=200,
            content_type="text/html; charset=utf-8",
            body=PRODUCT_HTML,
            crawl_ms=42,
        )

        self.assertEqual(metadata.title, "Cuisinart CPT-122 Compact 2-Slice Toaster")
        self.assertEqual(metadata.description, "Compact toaster for kitchen counters with shade settings.")
        self.assertEqual(metadata.canonical_url, "https://www.amazon.com/dp/B009GQ034C")
        self.assertEqual(metadata.language, "en")
        self.assertEqual(metadata.headings["h1"], ["Cuisinart compact toaster"])
        self.assertEqual(metadata.json_ld[0]["@type"], "Product")
        self.assertGreater(metadata.word_count, 5)
        self.assertTrue(metadata.content_hash)

    def test_classifies_product_and_topics(self) -> None:
        metadata = extract_metadata(
            requested_url="https://www.amazon.com/dp/B009GQ034C",
            final_url="https://www.amazon.com/dp/B009GQ034C",
            status_code=200,
            content_type="text/html",
            body=PRODUCT_HTML,
            crawl_ms=10,
        )

        page = PageMetadata(
            url=metadata.requested_url,
            final_url=metadata.final_url,
            status_code=metadata.status_code,
            content_type=metadata.content_type,
            title=metadata.title,
            description=metadata.description,
            h1=metadata.headings["h1"],
            headings=metadata.headings["all"],
            body_text=metadata.body_text,
            meta=metadata.meta,
            json_ld=metadata.json_ld,
        )
        result = TopicClassifier().classify(page)

        self.assertEqual(result.page_type, "ecommerce")
        self.assertIn("cuisinart compact toaster", result.topics)

    def test_classifies_article_and_outdoors_topic(self) -> None:
        metadata = extract_metadata(
            requested_url="https://blog.rei.com/camp/how-to-introduce-your-indoorsy-friend-to-the-outdoors/",
            final_url="https://blog.rei.com/camp/how-to-introduce-your-indoorsy-friend-to-the-outdoors/",
            status_code=200,
            content_type="text/html",
            body=ARTICLE_HTML,
            crawl_ms=12,
        )

        page = PageMetadata(
            url=metadata.requested_url,
            final_url=metadata.final_url,
            status_code=metadata.status_code,
            content_type=metadata.content_type,
            title=metadata.title,
            description=metadata.description,
            h1=metadata.headings["h1"],
            headings=metadata.headings["all"],
            body_text=metadata.body_text,
            meta=metadata.meta,
            json_ld=metadata.json_ld,
        )
        result = TopicClassifier().classify(page)

        self.assertEqual(result.page_type, "outdoors")
        self.assertIn("camping friend", result.topics)


if __name__ == "__main__":
    unittest.main()
