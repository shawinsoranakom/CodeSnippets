def test_truncate_html_words(self):
        truncator = text.Truncator(
            '<p id="par"><strong><em>The quick brown fox jumped over the lazy dog.</em>'
            "</strong></p>"
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick brown fox jumped over the lazy dog.</em>'
            "</strong></p>",
            truncator.words(10, html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick brown fox…</em></strong></p>',
            truncator.words(4, html=True),
        )
        self.assertEqual(
            "",
            truncator.words(0, html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick brown fox....</em></strong></p>',
            truncator.words(4, "....", html=True),
        )
        self.assertEqual(
            '<p id="par"><strong><em>The quick brown fox</em></strong></p>',
            truncator.words(4, "", html=True),
        )

        truncator = text.Truncator(
            "<p>The  quick \t brown fox jumped over the lazy dog.</p>"
        )
        self.assertEqual(
            "<p>The quick brown fox…</p>",
            truncator.words(4, html=True),
        )

        # Test with new line inside tag
        truncator = text.Truncator(
            '<p>The quick <a href="xyz.html"\n id="mylink">brown fox</a> jumped over '
            "the lazy dog.</p>"
        )
        self.assertEqual(
            '<p>The quick <a href="xyz.html"\n id="mylink">brown…</a></p>',
            truncator.words(3, html=True),
        )
        self.assertEqual(
            "<p>The…</p>",
            truncator.words(1, html=True),
        )

        # Test self-closing tags
        truncator = text.Truncator(
            "<br/>The <hr />quick brown fox jumped over the lazy dog."
        )
        self.assertEqual("<br/>The <hr />quick brown…", truncator.words(3, html=True))
        truncator = text.Truncator(
            "<br>The <hr/>quick <em>brown fox</em> jumped over the lazy dog."
        )
        self.assertEqual(
            "<br>The <hr/>quick <em>brown…</em>", truncator.words(3, html=True)
        )

        # Test html entities
        truncator = text.Truncator(
            "<i>Buenos d&iacute;as! &#x00bf;C&oacute;mo est&aacute;?</i>"
        )
        self.assertEqual(
            "<i>Buenos días! ¿Cómo…</i>",
            truncator.words(3, html=True),
        )
        truncator = text.Truncator("<p>I &lt;3 python, what about you?</p>")
        self.assertEqual("<p>I &lt;3 python,…</p>", truncator.words(3, html=True))

        truncator = text.Truncator("foo</p>")
        self.assertEqual("foo</p>", truncator.words(3, html=True))

        # Only open brackets.
        truncator = text.Truncator("<" * 60_000)
        self.assertEqual(truncator.words(1, html=True), "&lt;…")

        # Tags with special chars in attrs.
        truncator = text.Truncator(
            """<i style="margin: 5%; font: *;">Hello, my dear lady!</i>"""
        )
        self.assertEqual(
            """<i style="margin: 5%; font: *;">Hello, my dear…</i>""",
            truncator.words(3, html=True),
        )

        # Tags with special non-latin chars in attrs.
        truncator = text.Truncator("""<p data-x="א">Hello, my dear lady!</p>""")
        self.assertEqual(
            """<p data-x="א">Hello, my dear…</p>""",
            truncator.words(3, html=True),
        )

        # Misplaced brackets.
        truncator = text.Truncator("hello >< world")
        self.assertEqual(truncator.words(1, html=True), "hello…")
        self.assertEqual(truncator.words(2, html=True), "hello &gt;…")
        self.assertEqual(truncator.words(3, html=True), "hello &gt;&lt;…")
        self.assertEqual(truncator.words(4, html=True), "hello &gt;&lt; world")