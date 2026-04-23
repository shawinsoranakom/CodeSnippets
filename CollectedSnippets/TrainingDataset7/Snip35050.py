def make_tests(self):
        """Return an iterable of tests."""
        suite = self.make_test_suite()
        return list(iter_test_cases(suite))