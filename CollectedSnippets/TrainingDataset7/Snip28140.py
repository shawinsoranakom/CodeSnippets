def test_IntegerField(self):
        lazy_func = lazy(lambda: 1, int)
        self.assertIsInstance(IntegerField().get_prep_value(lazy_func()), int)