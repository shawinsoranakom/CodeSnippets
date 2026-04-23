def test_decimalfield_changed(self):
        f = DecimalField(max_digits=2, decimal_places=2)
        d = decimal.Decimal("0.1")
        self.assertFalse(f.has_changed(d, "0.10"))
        self.assertTrue(f.has_changed(d, "0.101"))

        with translation.override("fr"):
            f = DecimalField(max_digits=2, decimal_places=2, localize=True)
            localized_d = formats.localize_input(d)  # -> '0,1' in French
            self.assertFalse(f.has_changed(d, localized_d))