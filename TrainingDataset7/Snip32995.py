def test_autoescape(self):
        self.assertEqual(
            linebreaks_filter("foo\n<a>bar</a>\nbuz"),
            "<p>foo<br>&lt;a&gt;bar&lt;/a&gt;<br>buz</p>",
        )