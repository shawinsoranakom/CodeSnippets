def test_truncate_chars_html_with_html_entities(self):
        truncator = text.Truncator(
            "<i>Buenos d&iacute;as! &#x00bf;C&oacute;mo est&aacute;?</i>"
        )
        self.assertEqual(
            "<i>Buenos días! ¿Cómo está?</i>",
            truncator.chars(40, html=True),
        )
        self.assertEqual(
            "<i>Buenos días…</i>",
            truncator.chars(12, html=True),
        )
        self.assertEqual(
            "<i>Buenos días! ¿Cómo está…</i>",
            truncator.chars(24, html=True),
        )
        truncator = text.Truncator("<p>I &lt;3 python, what about you?</p>")
        self.assertEqual("<p>I &lt;3 python, wh…</p>", truncator.chars(16, html=True))