def test_range(self):
        self.assertEqual(slice_filter("abcdefg", "1:2"), "b")