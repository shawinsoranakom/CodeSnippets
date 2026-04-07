def test_escape_uri_path(self):
        cases = [
            (
                "/;some/=awful/?path/:with/@lots/&of/+awful/chars",
                "/%3Bsome/%3Dawful/%3Fpath/:with/@lots/&of/+awful/chars",
            ),
            ("/foo#bar", "/foo%23bar"),
            ("/foo?bar", "/foo%3Fbar"),
        ]
        for uri, expected in cases:
            with self.subTest(uri):
                self.assertEqual(escape_uri_path(uri), expected)