def test_all_format_strings(self):
        all_locales = LANG_INFO.keys()
        some_date = datetime.date(2017, 10, 14)
        some_datetime = datetime.datetime(2017, 10, 14, 10, 23)
        for locale in all_locales:
            with self.subTest(locale=locale), translation.override(locale):
                self.assertIn(
                    "2017", date_format(some_date)
                )  # Uses DATE_FORMAT by default
                self.assertIn(
                    "23", time_format(some_datetime)
                )  # Uses TIME_FORMAT by default
                self.assertIn("2017", date_format(some_datetime, "DATETIME_FORMAT"))
                self.assertIn("2017", date_format(some_date, "YEAR_MONTH_FORMAT"))
                self.assertIn("14", date_format(some_date, "MONTH_DAY_FORMAT"))
                self.assertIn("2017", date_format(some_date, "SHORT_DATE_FORMAT"))
                self.assertIn(
                    "2017",
                    date_format(some_datetime, "SHORT_DATETIME_FORMAT"),
                )