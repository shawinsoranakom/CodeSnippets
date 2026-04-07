def test_lazy_bytes_and_str_result_classes(self):
        lazy_obj = lazy(lambda: "test", str, bytes)
        self.assertEqual(str(lazy_obj()), "test")