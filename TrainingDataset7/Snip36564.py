def test_common_large_number_of_words(self):
        """words(n) has n words when n is greater than len(WORDS)."""
        self.assertEqual(len(words(500).split()), 500)