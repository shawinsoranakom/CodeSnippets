def test_index_list_fails(self):
        with self.assertRaises(ValueError):
            index_([1, 2, 3, 4], 5)