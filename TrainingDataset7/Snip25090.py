def test_uncommon_locale_formats(self):
        testcases = {
            # French Canadian locale uses 'h' as time format separator.
            ("fr-ca", time_format, (self.t, "TIME_FORMAT")): "10\xa0h\xa015",
            (
                "fr-ca",
                date_format,
                (self.dt, "DATETIME_FORMAT"),
            ): "31 décembre 2009, 20\xa0h\xa050",
            (
                "fr-ca",
                date_format,
                (self.dt, "SHORT_DATETIME_FORMAT"),
            ): "2009-12-31 20\xa0h\xa050",
        }
        for testcase, expected in testcases.items():
            locale, format_function, format_args = testcase
            with self.subTest(locale=locale, expected=expected):
                with translation.override(locale, deactivate=True):
                    self.assertEqual(expected, format_function(*format_args))