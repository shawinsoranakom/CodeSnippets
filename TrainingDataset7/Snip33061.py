def test_negative_index(self):
        self.assertEqual(slice_filter("abcdefg", "-1"), "abcdef")