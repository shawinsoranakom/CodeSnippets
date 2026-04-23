def test_decimal_invalid_lower(self):
        field = pg_forms.DecimalRangeField()
        msg = "Enter a number."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["a", "3.1415926"])