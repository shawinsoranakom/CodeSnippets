def test_urlize09(self):
        output = self.engine.render_to_string(
            "urlize09", {"a": "http://example.com/?x=&amp;y=&lt;2&gt;"}
        )
        self.assertEqual(
            output,
            '<a href="http://example.com/?x=&amp;y=%3C2%3E" rel="nofollow">'
            "http://example.com/?x=&amp;y=&lt;2&gt;</a>",
        )