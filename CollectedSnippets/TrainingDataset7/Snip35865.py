def test_include_urls(self):
        self.assertEqual(include(self.url_patterns), (self.url_patterns, None, None))