def test_urlizetrunc01(self):
        output = self.engine.render_to_string(
            "urlizetrunc01",
            {
                "a": '"Unsafe" http://example.com/x=&y=',
                "b": mark_safe("&quot;Safe&quot; http://example.com?x=&amp;y="),
            },
        )
        self.assertEqual(
            output,
            '"Unsafe" '
            '<a href="http://example.com/x=&amp;y=" rel="nofollow">http://…</a> '
            "&quot;Safe&quot; "
            '<a href="http://example.com?x=&amp;y=" rel="nofollow">http://…</a>',
        )