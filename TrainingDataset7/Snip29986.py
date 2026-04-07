def test_datetime_open(self):
        field = pg_forms.DateTimeRangeField()
        value = field.clean(["", "2013-04-09 11:45"])
        self.assertEqual(
            value, DateTimeTZRange(None, datetime.datetime(2013, 4, 9, 11, 45))
        )