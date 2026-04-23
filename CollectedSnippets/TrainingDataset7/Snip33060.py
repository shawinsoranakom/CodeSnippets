def test_index_integer(self):
        self.assertEqual(slice_filter("abcdefg", 1), "a")