def test_datetime_required(self):
        field = pg_forms.DateTimeRangeField(required=True)
        msg = "This field is required."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["", ""])
        value = field.clean(["2013-04-09 11:45", ""])
        self.assertEqual(
            value, DateTimeTZRange(datetime.datetime(2013, 4, 9, 11, 45), None)
        )