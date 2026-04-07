def test_urlizetrunc02(self):
        output = self.engine.render_to_string(
            "urlizetrunc02",
            {
                "a": '"Unsafe" http://example.com/x=&y=',
                "b": mark_safe("&quot;Safe&quot; http://example.com?x=&amp;y="),
            },
        )
        self.assertEqual(
            output,
            '&quot;Unsafe&quot; <a href="http://example.com/x=&amp;y=" rel="nofollow">'
            "http://…</a> "
            '&quot;Safe&quot; <a href="http://example.com?x=&amp;y=" rel="nofollow">'
            "http://…</a>",
        )