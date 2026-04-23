def test_combine_and_both_empty(self):
        self.assertEqual(Q() & Q(), Q())