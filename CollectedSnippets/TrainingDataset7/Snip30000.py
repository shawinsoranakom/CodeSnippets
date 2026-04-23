def test_model_field_with_default_bounds(self):
        field = pg_forms.DateTimeRangeField(default_bounds="[]")
        value = field.clean(["2014-01-01 00:00:00", "2014-02-03 12:13:14"])
        lower = datetime.datetime(2014, 1, 1, 0, 0, 0)
        upper = datetime.datetime(2014, 2, 3, 12, 13, 14)
        self.assertEqual(value, DateTimeTZRange(lower, upper, "[]"))