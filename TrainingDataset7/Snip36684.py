def test_truncate_chars_html_with_newline_inside_tag(self):
        truncator = text.Truncator(
            '<p>The quick <a href="xyz.html"\n id="mylink">brown fox</a> jumped over '
            "the lazy dog.</p>"
        )
        self.assertEqual(
            '<p>The quick <a href="xyz.html"\n id="mylink">brow…</a></p>',
            truncator.chars(15, html=True),
        )
        self.assertEqual(
            "<p>Th…</p>",
            truncator.chars(3, html=True),
        )