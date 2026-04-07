def test_trailing_semicolon(self):
        self.assertEqual(
            urlize("http://example.com?x=&amp;", autoescape=False),
            '<a href="http://example.com?x=" rel="nofollow">'
            "http://example.com?x=&amp;</a>",
        )
        self.assertEqual(
            urlize("http://example.com?x=&amp;;", autoescape=False),
            '<a href="http://example.com?x=" rel="nofollow">'
            "http://example.com?x=&amp;</a>;",
        )
        self.assertEqual(
            urlize("http://example.com?x=&amp;;;", autoescape=False),
            '<a href="http://example.com?x=" rel="nofollow">'
            "http://example.com?x=&amp;</a>;;",
        )
        self.assertEqual(
            urlize("http://example.com?x=&amp.;...;", autoescape=False),
            '<a href="http://example.com?x=" rel="nofollow">'
            "http://example.com?x=&amp</a>.;...;",
        )