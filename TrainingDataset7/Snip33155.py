def test_invalid_number(self):
        self.assertEqual(
            truncatewords("A sentence with a few words in it", "not a number"),
            "A sentence with a few words in it",
        )