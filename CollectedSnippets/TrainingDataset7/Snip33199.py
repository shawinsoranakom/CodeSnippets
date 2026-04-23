def test_urlize01(self):
        output = self.engine.render_to_string(
            "urlize01",
            {
                "a": "http://example.com/?x=&y=",
                "b": mark_safe("http://example.com?x=&amp;y=&lt;2&gt;"),
            },
        )
        self.assertEqual(
            output,
            '<a href="http://example.com/?x=&amp;y=" rel="nofollow">'
            "http://example.com/?x=&y=</a> "
            '<a href="http://example.com?x=&amp;y=%3C2%3E" rel="nofollow">'
            "http://example.com?x=&amp;y=&lt;2&gt;</a>",
        )