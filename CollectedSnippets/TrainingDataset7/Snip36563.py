def test_more_words_than_common(self):
        """words(n) returns n words for n > 19."""
        self.assertEqual(len(words(25).split()), 25)