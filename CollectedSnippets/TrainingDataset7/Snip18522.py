def test_adapt_unknown_value_date(self):
        value = timezone.now().date()
        self.assertEqual(
            self.ops.adapt_unknown_value(value), self.ops.adapt_datefield_value(value)
        )