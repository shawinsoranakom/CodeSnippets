def test_zero_values(self):
        self.assertEqual(floatformat(0, 6), "0.000000")
        self.assertEqual(floatformat(0, 7), "0.0000000")
        self.assertEqual(floatformat(0, 10), "0.0000000000")
        self.assertEqual(
            floatformat(0.000000000000000000015, 20), "0.00000000000000000002"
        )
        self.assertEqual(floatformat("0.00", 0), "0")
        self.assertEqual(floatformat(Decimal("0.00"), 0), "0")
        self.assertEqual(floatformat("0.0000", 2), "0.00")
        self.assertEqual(floatformat(Decimal("0.0000"), 2), "0.00")
        self.assertEqual(floatformat("0.000000", 4), "0.0000")
        self.assertEqual(floatformat(Decimal("0.000000"), 4), "0.0000")