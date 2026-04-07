def test_date_invalid_lower(self):
        field = pg_forms.DateRangeField()
        msg = "Enter a valid date."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["a", "2013-04-09"])