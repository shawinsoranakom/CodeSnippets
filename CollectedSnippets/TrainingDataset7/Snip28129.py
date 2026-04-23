def test_BinaryField(self):
        lazy_func = lazy(lambda: b"", bytes)
        self.assertIsInstance(BinaryField().get_prep_value(lazy_func()), bytes)