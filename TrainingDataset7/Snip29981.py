def test_date_invalid_upper(self):
        field = pg_forms.DateRangeField()
        msg = "Enter a valid date."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["2013-04-09", "b"])