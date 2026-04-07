def test_decimals(self):
        self.assertEqual(pluralize(Decimal(1)), "")
        self.assertEqual(pluralize(Decimal(0)), "s")
        self.assertEqual(pluralize(Decimal(2)), "s")