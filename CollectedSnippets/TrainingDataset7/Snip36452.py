def test(self):
        tests = (
            ("//example.com", "/%2Fexample.com"),
            ("//", "/%2F"),
        )
        for url, expected in tests:
            with self.subTest(url=url):
                self.assertEqual(escape_leading_slashes(url), expected)