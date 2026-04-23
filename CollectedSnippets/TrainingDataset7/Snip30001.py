def test_has_changed(self):
        for field, value in (
            (pg_forms.DateRangeField(), ["2010-01-01", "2020-12-12"]),
            (pg_forms.DateTimeRangeField(), ["2010-01-01 11:13", "2020-12-12 14:52"]),
            (pg_forms.IntegerRangeField(), [1, 2]),
            (pg_forms.DecimalRangeField(), ["1.12345", "2.001"]),
        ):
            with self.subTest(field=field.__class__.__name__):
                self.assertTrue(field.has_changed(None, value))
                self.assertTrue(field.has_changed([value[0], ""], value))
                self.assertTrue(field.has_changed(["", value[1]], value))
                self.assertFalse(field.has_changed(value, value))