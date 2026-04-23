def test_valid_dates(self):
        field = pg_forms.DateRangeField()
        value = field.clean(["01/01/2014", "02/02/2014"])
        lower = datetime.date(2014, 1, 1)
        upper = datetime.date(2014, 2, 2)
        self.assertEqual(value, DateRange(lower, upper))