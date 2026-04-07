def test_TimeField(self):
        lazy_func = lazy(lambda: datetime.datetime.now().time(), datetime.time)
        self.assertIsInstance(TimeField().get_prep_value(lazy_func()), datetime.time)