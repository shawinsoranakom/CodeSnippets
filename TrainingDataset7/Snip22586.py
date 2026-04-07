def test_floatfield_support_decimal_separator(self):
        with translation.override(None):
            f = FloatField(localize=True)
            self.assertEqual(f.clean("1001,10"), 1001.10)
            self.assertEqual(f.clean("1001.10"), 1001.10)