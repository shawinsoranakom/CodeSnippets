def test_paragraphs_not_common(self, mock_randint, mock_choice, mock_sample):
        """
        paragraphs(1, common=False) generating one paragraph that's not the
        COMMON_P paragraph.
        """
        # Make creating 2 sentences use 2 phrases.
        mock_randint.return_value = 2
        mock_sample.return_value = ["exercitationem", "perferendis"]
        mock_choice.return_value = "."
        self.assertEqual(
            paragraphs(1, common=False),
            [
                "Exercitationem perferendis, exercitationem perferendis. "
                "Exercitationem perferendis, exercitationem perferendis."
            ],
        )
        self.assertEqual(mock_randint.call_count, 7)