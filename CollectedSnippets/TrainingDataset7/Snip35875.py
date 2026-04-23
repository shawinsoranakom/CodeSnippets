def test_invalid_resolve(self):
        test_urls = [
            "/lookahead-/not-a-city/",
            "/lookbehind-/not-a-city/",
            "/lookahead+/other-city/",
            "/lookbehind+/other-city/",
        ]
        for test_url in test_urls:
            with self.subTest(url=test_url):
                with self.assertRaises(Resolver404):
                    resolve(test_url)