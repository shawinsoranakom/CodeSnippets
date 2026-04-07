def test_zero_length(self):
        self.assertEqual(slice_filter("abcdefg", "0"), "")