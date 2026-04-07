def test_not_common_words(self, mock_sample):
        """words(n, common=False) returns random words."""
        mock_sample.return_value = ["exercitationem", "perferendis"]
        self.assertEqual(words(2, common=False), "exercitationem perferendis")