def test_autoescape(self):
        self.assertEqual(
            linenumbers("foo\n<a>bar</a>\nbuz"),
            "1. foo\n2. &lt;a&gt;bar&lt;/a&gt;\n3. buz",
        )