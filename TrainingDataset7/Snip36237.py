def test_y_format_year_before_1000(self):
        tests = [
            (476, "76"),
            (42, "42"),
            (4, "04"),
        ]
        for year, expected_date in tests:
            with self.subTest(year=year):
                self.assertEqual(
                    dateformat.format(datetime(year, 9, 8, 5, 0), "y"),
                    expected_date,
                )