def test_lazy_str_cast_mixed_bytes_result_types(self):
        lazy_value = lazy(lambda: [1], bytes, list)()
        self.assertEqual(str(lazy_value), "[1]")