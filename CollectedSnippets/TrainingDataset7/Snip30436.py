def test_combine_xor_both_empty(self):
        self.assertEqual(Q() ^ Q(), Q())