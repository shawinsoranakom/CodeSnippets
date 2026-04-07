def test_FileField(self):
        lazy_func = lazy(lambda: "filename.ext", str)
        self.assertIsInstance(FileField().get_prep_value(lazy_func()), str)
        lazy_func = lazy(lambda: 0, int)
        self.assertIsInstance(FileField().get_prep_value(lazy_func()), str)