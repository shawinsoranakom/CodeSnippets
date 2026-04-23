def assert_non_localized_year(self, response, year):
        """
        The year is not localized with USE_THOUSAND_SEPARATOR (#15234).
        """
        self.assertNotContains(response, formats.number_format(year))