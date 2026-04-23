def test_truncate(self):
        self.assertEqual(truncatewords("A sentence with a few words in it", 1), "A …")