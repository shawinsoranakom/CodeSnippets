def test_ImageField(self):
        lazy_func = lazy(lambda: "filename.ext", str)
        self.assertIsInstance(ImageField().get_prep_value(lazy_func()), str)