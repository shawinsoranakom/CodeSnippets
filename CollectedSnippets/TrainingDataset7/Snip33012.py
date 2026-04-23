def test_autoescape_off(self):
        self.assertEqual(
            linenumbers("foo\n<a>bar</a>\nbuz", autoescape=False),
            "1. foo\n2. <a>bar</a>\n3. buz",
        )