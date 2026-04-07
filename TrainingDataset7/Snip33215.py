def test_unicode(self):
        self.assertEqual(
            urlize("https://en.wikipedia.org/wiki/Café"),
            '<a href="https://en.wikipedia.org/wiki/Caf%C3%A9" rel="nofollow">'
            "https://en.wikipedia.org/wiki/Café</a>",
        )