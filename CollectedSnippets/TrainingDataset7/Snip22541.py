def test_decimalfield_support_decimal_separator(self):
        with translation.override(None):
            f = DecimalField(localize=True)
            self.assertEqual(f.clean("1001,10"), decimal.Decimal("1001.10"))
            self.assertEqual(f.clean("1001.10"), decimal.Decimal("1001.10"))