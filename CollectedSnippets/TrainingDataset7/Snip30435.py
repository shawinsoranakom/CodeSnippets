def test_combine_or_both_empty(self):
        self.assertEqual(Q() | Q(), Q())