def test_hash_item_key(self):
        cases = [
            (lambda x: x, "64ad3fb166ddb41a2ca24f1803b8b722"),
            (lambda x: x.upper(), "ee22e8597bff91742affe4befbf4649a"),
        ]
        for key, expected in cases:
            with self.subTest(key=key):
                shuffler = Shuffler(seed=1234)
                actual = shuffler._hash_item("abc", key)
                self.assertEqual(actual, expected)