def test_decimalfield_support_thousands_separator(self):
        with translation.override(None):
            f = DecimalField(localize=True)
            self.assertEqual(f.clean("1.001,10"), decimal.Decimal("1001.10"))
            msg = "'Enter a number.'"
            with self.assertRaisesMessage(ValidationError, msg):
                f.clean("1,001.1")