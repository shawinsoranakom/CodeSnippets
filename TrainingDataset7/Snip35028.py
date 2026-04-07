def test_hash_text(self):
        actual = Shuffler._hash_text("abcd")
        self.assertEqual(actual, "e2fc714c4727ee9395f324cd2e7f331f")