def test_datetime_invalid_upper(self):
        field = pg_forms.DateTimeRangeField()
        msg = "Enter a valid date/time."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["2013-04-09 11:45", "sweet pickles"])