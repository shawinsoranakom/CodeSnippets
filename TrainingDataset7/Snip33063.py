def test_range_multiple(self):
        self.assertEqual(slice_filter("abcdefg", "1:3"), "bc")