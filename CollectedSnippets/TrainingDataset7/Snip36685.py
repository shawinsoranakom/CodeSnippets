def test_truncate_chars_html_with_void_elements(self):
        truncator = text.Truncator(
            "<br/>The <hr />quick brown fox jumped over the lazy dog."
        )
        self.assertEqual("<br/>The <hr />quick brown…", truncator.chars(16, html=True))
        truncator = text.Truncator(
            "<br>The <hr/>quick <em>brown fox</em> jumped over the lazy dog."
        )
        self.assertEqual(
            "<br>The <hr/>quick <em>brown…</em>", truncator.chars(16, html=True)
        )
        self.assertEqual("<br>The <hr/>q…", truncator.chars(6, html=True))
        self.assertEqual("<br>The <hr/>…", truncator.chars(5, html=True))
        self.assertEqual("<br>The…", truncator.chars(4, html=True))
        self.assertEqual("<br>Th…", truncator.chars(3, html=True))