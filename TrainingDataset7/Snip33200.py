def test_urlize02(self):
        output = self.engine.render_to_string(
            "urlize02",
            {
                "a": "http://example.com/?x=&y=",
                "b": mark_safe("http://example.com?x=&amp;y="),
            },
        )
        self.assertEqual(
            output,
            '<a href="http://example.com/?x=&amp;y=" rel="nofollow">'
            "http://example.com/?x=&amp;y=</a> "
            '<a href="http://example.com?x=&amp;y=" rel="nofollow">'
            "http://example.com?x=&amp;y=</a>",
        )