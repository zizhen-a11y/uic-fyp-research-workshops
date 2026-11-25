import unittest
from app import create_app


class GoogleTagTests(unittest.TestCase):
    def homepage(self, measurement_id):
        app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://",
                          "GA4_MEASUREMENT_ID": measurement_id})
        return app.test_client().get("/").get_data(as_text=True)

    def test_disabled_or_invalid(self):
        for value in ("", 'G-X"><script>'):
            self.assertNotIn("googletagmanager.com", self.homepage(value))

    def test_single_config_and_loader(self):
        html = self.homepage("G-C05T96EVF8")
        self.assertEqual(html.count("gtag/js?id=G-C05T96EVF8"), 1)
        self.assertEqual(html.count('gtag("config", "G-C05T96EVF8"'), 1)
        self.assertNotIn('"page_view"', html)
