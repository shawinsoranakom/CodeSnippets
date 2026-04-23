def test_date_has_changed_last(self):
        self.assertTrue(
            pg_forms.DateRangeField().has_changed(
                ["2010-01-01", "2020-12-12"],
                ["2010-01-01", "2020-12-31"],
            )
        )