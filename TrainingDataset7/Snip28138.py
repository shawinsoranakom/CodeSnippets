def test_FloatField(self):
        lazy_func = lazy(lambda: 1.2, float)
        self.assertIsInstance(FloatField().get_prep_value(lazy_func()), float)