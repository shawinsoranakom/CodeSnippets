def test_DecimalField(self):
        lazy_func = lazy(lambda: Decimal("1.2"), Decimal)
        self.assertIsInstance(DecimalField().get_prep_value(lazy_func()), Decimal)