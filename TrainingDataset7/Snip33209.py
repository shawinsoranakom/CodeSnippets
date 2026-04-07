def test_url_split_chars(self):
        # Quotes (single and double) and angle brackets shouldn't be considered
        # part of URLs.
        self.assertEqual(
            urlize('www.server.com"abc'),
            '<a href="https://www.server.com" rel="nofollow">www.server.com</a>&quot;'
            "abc",
        )
        self.assertEqual(
            urlize("www.server.com'abc"),
            '<a href="https://www.server.com" rel="nofollow">www.server.com</a>&#x27;'
            "abc",
        )
        self.assertEqual(
            urlize("www.server.com<abc"),
            '<a href="https://www.server.com" rel="nofollow">www.server.com</a>&lt;abc',
        )
        self.assertEqual(
            urlize("www.server.com>abc"),
            '<a href="https://www.server.com" rel="nofollow">www.server.com</a>&gt;abc',
        )