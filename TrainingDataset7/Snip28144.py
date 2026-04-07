def test_PositiveSmallIntegerField(self):
        lazy_func = lazy(lambda: 1, int)
        self.assertIsInstance(
            PositiveSmallIntegerField().get_prep_value(lazy_func()), int
        )