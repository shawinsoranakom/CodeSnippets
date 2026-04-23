def test_DateField(self):
        lazy_func = lazy(lambda: datetime.date.today(), datetime.date)
        self.assertIsInstance(DateField().get_prep_value(lazy_func()), datetime.date)