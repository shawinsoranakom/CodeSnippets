def test_floatfield_support_thousands_separator(self):
        with translation.override(None):
            f = FloatField(localize=True)
            self.assertEqual(f.clean("1.001,10"), 1001.10)
            msg = "'Enter a number.'"
            with self.assertRaisesMessage(ValidationError, msg):
                f.clean("1,001.1")