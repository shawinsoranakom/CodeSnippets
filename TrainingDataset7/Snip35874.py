def test_valid_resolve(self):
        test_urls = [
            "/lookahead-/a-city/",
            "/lookbehind-/a-city/",
            "/lookahead+/a-city/",
            "/lookbehind+/a-city/",
        ]
        for test_url in test_urls:
            with self.subTest(url=test_url):
                self.assertEqual(resolve(test_url).kwargs, {"city": "a-city"})