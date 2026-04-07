def test_truncate_chars_html(self):
        truncator = text.Truncator(
            '<p id="par"><strong><em>The quick brown fox jumped over the lazy dog.</em>'
            "</strong></p>"
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick brown fox jumped over the lazy dog.</em>'
            "</strong></p>",
            truncator.chars(80, html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick brown fox jumped over the lazy dog.</em>'
            "</strong></p>",
            truncator.chars(46, html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick brown fox jumped over the lazy dog…</em>'
            "</strong></p>",
            truncator.chars(45, html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick…</em></strong></p>',
            truncator.chars(10, html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>…</em></strong></p>',
            truncator.chars(1, html=True),
        )
        self.assertEqual("", truncator.chars(0, html=True))
        self.assertEqual("", truncator.chars(-1, html=True))
        self.assertEqual(
            '<p id="par"><strong><em>The qu....</em></strong></p>',
            truncator.chars(10, "....", html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick </em></strong></p>',
            truncator.chars(10, "", html=True),
        )
        truncator = text.Truncator("foo</p>")
        self.assertEqual("foo</p>", truncator.chars(5, html=True))