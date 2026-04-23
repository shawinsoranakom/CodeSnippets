def test_decimal_invalid_upper(self):
        field = pg_forms.DecimalRangeField()
        msg = "Enter a number."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["1.61803399", "b"])