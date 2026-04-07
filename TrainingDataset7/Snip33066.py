def test_empty_dict(self):
        self.assertEqual(slice_filter({}, "1"), {})