def test_valid_reverse(self):
        test_urls = [
            ("lookahead-positive", {"city": "a-city"}, "/lookahead+/a-city/"),
            ("lookahead-negative", {"city": "a-city"}, "/lookahead-/a-city/"),
            ("lookbehind-positive", {"city": "a-city"}, "/lookbehind+/a-city/"),
            ("lookbehind-negative", {"city": "a-city"}, "/lookbehind-/a-city/"),
        ]
        for name, kwargs, expected in test_urls:
            with self.subTest(name=name, kwargs=kwargs):
                self.assertEqual(reverse(name, kwargs=kwargs), expected)