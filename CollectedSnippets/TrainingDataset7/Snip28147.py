def test_SmallIntegerField(self):
        lazy_func = lazy(lambda: 1, int)
        self.assertIsInstance(SmallIntegerField().get_prep_value(lazy_func()), int)