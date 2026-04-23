def test_valid_timestamps(self):
        field = pg_forms.DateTimeRangeField()
        value = field.clean(["01/01/2014 00:00:00", "02/02/2014 12:12:12"])
        lower = datetime.datetime(2014, 1, 1, 0, 0, 0)
        upper = datetime.datetime(2014, 2, 2, 12, 12, 12)
        self.assertEqual(value, DateTimeTZRange(lower, upper))