def test_range_step(self):
        self.assertEqual(slice_filter("abcdefg", "0::2"), "aceg")