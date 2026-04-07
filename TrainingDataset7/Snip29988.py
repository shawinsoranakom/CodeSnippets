def test_datetime_invalid_lower(self):
        field = pg_forms.DateTimeRangeField()
        msg = "Enter a valid date/time."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["45", "2013-04-09 11:45"])