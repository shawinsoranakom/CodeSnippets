def test_sentence_ending(self, mock_choice):
        """Sentences end with a question mark or a period."""
        mock_choice.return_value = "?"
        self.assertIn(sentence()[-1], "?")
        mock_choice.return_value = "."
        self.assertIn(sentence()[-1], ".")