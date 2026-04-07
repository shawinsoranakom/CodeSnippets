def test_PositiveBigIntegerField(self):
        lazy_func = lazy(lambda: 1, int)
        self.assertIsInstance(
            PositiveBigIntegerField().get_prep_value(lazy_func()), int
        )