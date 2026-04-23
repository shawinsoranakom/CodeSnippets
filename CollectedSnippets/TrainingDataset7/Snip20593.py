def test_coalesce_idempotent(self):
        pair = ConcatPair(V("a"), V("b"))
        # Check nodes counts
        self.assertEqual(len(list(pair.flatten())), 3)
        self.assertEqual(
            len(list(pair.coalesce().flatten())), 7
        )  # + 2 Coalesce + 2 Value()
        self.assertEqual(len(list(pair.flatten())), 3)