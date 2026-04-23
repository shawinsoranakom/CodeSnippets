def test_index_tuple_fails(self):
        with self.assertRaises(ValueError):
            index_((1, 2, 3, 4), 5)