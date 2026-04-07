def mark_expected_failures_and_skips(self):
        """
        Mark tests in Django's test suite which are expected failures on this
        database and test which should be skipped on this database.
        """
        for test_name in self.connection.features.django_test_expected_failures:
            self._mark_test(test_name)
        for reason, tests in self.connection.features.django_test_skips.items():
            for test_name in tests:
                self._mark_test(test_name, reason)