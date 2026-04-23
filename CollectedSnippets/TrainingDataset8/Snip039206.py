def test_index_tuple(self):
        self.assertEqual(index_((1, 2, 3, 4), 1), 0)
        self.assertEqual(index_((1, 2, 3, 4), 4), 3)