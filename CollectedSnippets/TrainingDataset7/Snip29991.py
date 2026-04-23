def test_datetime_prepare_value(self):
        field = pg_forms.DateTimeRangeField()
        value = field.prepare_value(
            DateTimeTZRange(
                datetime.datetime(2015, 5, 22, 16, 6, 33, tzinfo=datetime.UTC),
                None,
            )
        )
        self.assertEqual(value, [datetime.datetime(2015, 5, 22, 18, 6, 33), None])