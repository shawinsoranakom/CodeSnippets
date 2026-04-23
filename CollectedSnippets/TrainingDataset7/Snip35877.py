def test_invalid_reverse(self):
        test_urls = [
            ("lookahead-positive", {"city": "other-city"}),
            ("lookahead-negative", {"city": "not-a-city"}),
            ("lookbehind-positive", {"city": "other-city"}),
            ("lookbehind-negative", {"city": "not-a-city"}),
        ]
        for name, kwargs in test_urls:
            with self.subTest(name=name, kwargs=kwargs):
                with self.assertRaises(NoReverseMatch):
                    reverse(name, kwargs=kwargs)