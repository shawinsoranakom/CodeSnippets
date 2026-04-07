def test_paragraph(self, mock_paragraph_randint, mock_choice, mock_sample):
        """paragraph() generates a single paragraph."""
        # Make creating 2 sentences use 2 phrases.
        mock_paragraph_randint.return_value = 2
        mock_sample.return_value = ["exercitationem", "perferendis"]
        mock_choice.return_value = "."
        value = paragraph()
        self.assertEqual(mock_paragraph_randint.call_count, 7)
        self.assertEqual(
            value,
            (
                "Exercitationem perferendis, exercitationem perferendis. "
                "Exercitationem perferendis, exercitationem perferendis."
            ),
        )