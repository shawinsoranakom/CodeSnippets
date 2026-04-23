def test_truncate_words(self):
        truncator = text.Truncator("The quick brown fox jumped over the lazy dog.")
        self.assertEqual(
            "The quick brown fox jumped over the lazy dog.", truncator.words(10)
        )
        self.assertEqual("The quick brown fox…", truncator.words(4))
        self.assertEqual("The quick brown fox[snip]", truncator.words(4, "[snip]"))
        # lazy strings are handled correctly
        truncator = text.Truncator(
            lazystr("The quick brown fox jumped over the lazy dog.")
        )
        self.assertEqual("The quick brown fox…", truncator.words(4))
        self.assertEqual("", truncator.words(0))
        self.assertEqual("", truncator.words(-1))