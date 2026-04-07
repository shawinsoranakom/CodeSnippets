def test_datetime_has_changed_first(self):
        self.assertTrue(
            pg_forms.DateTimeRangeField().has_changed(
                ["2010-01-01 00:00", "2020-12-12 00:00"],
                ["2010-01-31 23:00", "2020-12-12 00:00"],
            )
        )