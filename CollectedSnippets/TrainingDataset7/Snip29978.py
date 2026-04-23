def test_date_open(self):
        field = pg_forms.DateRangeField()
        value = field.clean(["", "2013-04-09"])
        self.assertEqual(value, DateRange(None, datetime.date(2013, 4, 9)))