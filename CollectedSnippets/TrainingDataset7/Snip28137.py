def test_FilePathField(self):
        lazy_func = lazy(lambda: "tests.py", str)
        self.assertIsInstance(FilePathField().get_prep_value(lazy_func()), str)
        lazy_func = lazy(lambda: 0, int)
        self.assertIsInstance(FilePathField().get_prep_value(lazy_func()), str)