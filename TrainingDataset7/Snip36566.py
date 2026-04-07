def test_sentence_starts_with_capital(self):
        """A sentence starts with a capital letter."""
        self.assertTrue(sentence()[0].isupper())