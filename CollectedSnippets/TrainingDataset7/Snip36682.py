def test_truncate_chars(self):
        truncator = text.Truncator("The quick brown fox jumped over the lazy dog.")
        self.assertEqual(
            "The quick brown fox jumped over the lazy dog.", truncator.chars(100)
        ),
        self.assertEqual("The quick brown fox …", truncator.chars(21))
        self.assertEqual("The quick brown fo.....", truncator.chars(23, "....."))
        self.assertEqual(".....", truncator.chars(4, "....."))

        nfc = text.Truncator("o\xfco\xfco\xfco\xfc")
        nfd = text.Truncator("ou\u0308ou\u0308ou\u0308ou\u0308")
        self.assertEqual("oüoüoüoü", nfc.chars(8))
        self.assertEqual("oüoüoüoü", nfd.chars(8))
        self.assertEqual("oü…", nfc.chars(3))
        self.assertEqual("oü…", nfd.chars(3))

        # Ensure the final length is calculated correctly when there are
        # combining characters with no precomposed form, and that combining
        # characters are not split up.
        truncator = text.Truncator("-B\u030aB\u030a----8")
        self.assertEqual("-B\u030a…", truncator.chars(3))
        self.assertEqual("-B\u030aB\u030a-…", truncator.chars(5))
        self.assertEqual("-B\u030aB\u030a----8", truncator.chars(8))

        # Ensure the length of the end text is correctly calculated when it
        # contains combining characters with no precomposed form.
        truncator = text.Truncator("-----")
        self.assertEqual("---B\u030a", truncator.chars(4, "B\u030a"))
        self.assertEqual("-----", truncator.chars(5, "B\u030a"))

        # Make a best effort to shorten to the desired length, but requesting
        # a length shorter than the ellipsis shouldn't break
        self.assertEqual("...", text.Truncator("asdf").chars(1, truncate="..."))
        # lazy strings are handled correctly
        self.assertEqual(
            text.Truncator(lazystr("The quick brown fox")).chars(10), "The quick…"
        )