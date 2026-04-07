def test_static_quotes_urls(self):
        output = self.engine.render_to_string("static-statictag05")
        self.assertEqual(
            output,
            urljoin(settings.STATIC_URL, "/static/special%3Fchars%26quoted.html"),
        )