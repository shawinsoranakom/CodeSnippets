def test_autoescape(self):
        self.assertEqual(
            linebreaksbr("foo\n<a>bar</a>\nbuz"),
            "foo<br>&lt;a&gt;bar&lt;/a&gt;<br>buz",
        )