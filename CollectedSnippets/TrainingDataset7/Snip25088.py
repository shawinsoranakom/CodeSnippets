def test_false_like_locale_formats(self):
        """
        The active locale's formats take precedence over the default settings
        even if they would be interpreted as False in a conditional test
        (e.g. 0 or empty string) (#16938).
        """
        with translation.override("fr"):
            with self.settings(USE_THOUSAND_SEPARATOR=True, THOUSAND_SEPARATOR="!"):
                self.assertEqual("\xa0", get_format("THOUSAND_SEPARATOR"))
                # Even a second time (after the format has been cached)...
                self.assertEqual("\xa0", get_format("THOUSAND_SEPARATOR"))

            with self.settings(FIRST_DAY_OF_WEEK=0):
                self.assertEqual(1, get_format("FIRST_DAY_OF_WEEK"))
                # Even a second time (after the format has been cached)...
                self.assertEqual(1, get_format("FIRST_DAY_OF_WEEK"))