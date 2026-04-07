def test_adapt_unknown_value_decimal(self):
        value = decimal.Decimal("3.14")
        self.assertEqual(
            self.ops.adapt_unknown_value(value),
            self.ops.adapt_decimalfield_value(value),
        )