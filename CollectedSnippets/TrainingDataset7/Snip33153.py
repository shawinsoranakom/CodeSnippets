def test_truncate2(self):
        self.assertEqual(
            truncatewords("A sentence with a few words in it", 5),
            "A sentence with a few …",
        )