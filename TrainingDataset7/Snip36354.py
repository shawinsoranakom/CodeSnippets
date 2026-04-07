def test_lazy_str_cast_mixed_result_types(self):
        lazy_value = lazy(lambda: [1], str, list)()
        self.assertEqual(str(lazy_value), "[1]")