def test_floatfield_changed(self):
        f = FloatField()
        n = 4.35
        self.assertFalse(f.has_changed(n, "4.3500"))

        with translation.override("fr"):
            f = FloatField(localize=True)
            localized_n = formats.localize_input(n)  # -> '4,35' in French
            self.assertFalse(f.has_changed(n, localized_n))