def test_autoescape_off(self):
        self.assertEqual(
            linebreaks_filter("foo\n<a>bar</a>\nbuz", autoescape=False),
            "<p>foo<br><a>bar</a><br>buz</p>",
        )