def test_hash_item_seed(self):
        cases = [
            (1234, "64ad3fb166ddb41a2ca24f1803b8b722"),
            # Passing a string gives the same value.
            ("1234", "64ad3fb166ddb41a2ca24f1803b8b722"),
            (5678, "4dde450ad339b6ce45a0a2666e35b975"),
        ]
        for seed, expected in cases:
            with self.subTest(seed=seed):
                shuffler = Shuffler(seed=seed)
                actual = shuffler._hash_item("abc", lambda x: x)
                self.assertEqual(actual, expected)