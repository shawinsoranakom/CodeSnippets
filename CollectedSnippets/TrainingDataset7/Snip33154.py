def test_overtruncate(self):
        self.assertEqual(
            truncatewords("A sentence with a few words in it", 100),
            "A sentence with a few words in it",
        )