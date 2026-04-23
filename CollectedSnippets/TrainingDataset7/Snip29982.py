def test_date_required(self):
        field = pg_forms.DateRangeField(required=True)
        msg = "This field is required."
        with self.assertRaisesMessage(exceptions.ValidationError, msg):
            field.clean(["", ""])
        value = field.clean(["1976-04-16", ""])
        self.assertEqual(value, DateRange(datetime.date(1976, 4, 16), None))