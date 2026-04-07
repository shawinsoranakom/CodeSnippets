def test_decimalfield_scientific(self):
        f = DecimalField(max_digits=4, decimal_places=2)
        with self.assertRaisesMessage(ValidationError, "Ensure that there are no more"):
            f.clean("1E+2")
        self.assertEqual(f.clean("1E+1"), decimal.Decimal("10"))
        self.assertEqual(f.clean("1E-1"), decimal.Decimal("0.1"))
        self.assertEqual(f.clean("0.546e+2"), decimal.Decimal("54.6"))