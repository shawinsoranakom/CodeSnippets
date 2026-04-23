def test_fail_silently(self):
        obj = object()
        self.assertEqual(slice_filter(obj, "0::2"), obj)