def test_sentence(self, mock_randint, mock_choice, mock_sample):
        """
        Sentences are built using some number of phrases and a set of words.
        """
        mock_randint.return_value = 2  # Use two phrases.
        mock_sample.return_value = ["exercitationem", "perferendis"]
        mock_choice.return_value = "?"
        value = sentence()
        self.assertEqual(mock_randint.call_count, 3)
        self.assertEqual(mock_sample.call_count, 2)
        self.assertEqual(mock_choice.call_count, 1)
        self.assertEqual(
            value, "Exercitationem perferendis, exercitationem perferendis?"
        )