def test_autoescape_off(self):
        self.assertEqual(
            linebreaksbr("foo\n<a>bar</a>\nbuz", autoescape=False),
            "foo<br><a>bar</a><br>buz",
        )