def test_decimal_open(self):
        field = pg_forms.DecimalRangeField()
        value = field.clean(["", "3.1415926"])
        self.assertEqual(value, NumericRange(None, Decimal("3.1415926")))