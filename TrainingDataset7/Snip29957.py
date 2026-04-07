def test_valid_decimal(self):
        field = pg_forms.DecimalRangeField()
        value = field.clean(["1.12345", "2.001"])
        self.assertEqual(value, NumericRange(Decimal("1.12345"), Decimal("2.001")))