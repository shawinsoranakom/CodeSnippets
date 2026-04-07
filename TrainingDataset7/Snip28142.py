def test_GenericIPAddressField(self):
        lazy_func = lazy(lambda: "127.0.0.1", str)
        self.assertIsInstance(GenericIPAddressField().get_prep_value(lazy_func()), str)
        lazy_func = lazy(lambda: 0, int)
        self.assertIsInstance(GenericIPAddressField().get_prep_value(lazy_func()), str)