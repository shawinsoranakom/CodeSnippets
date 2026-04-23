def __sub__(self, other: TestRun) -> TestRun:
        """
        To subtract test runs means to run all the tests in the first run except for what the second run specifies.
        """

        # Is any file empty?
        if self.is_empty():
            return TestRun.empty()
        if other.is_empty():
            return copy(self)

        # Are you trying to subtract tests that don't even exist in this test run?
        if self.test_file != other.test_file:
            return copy(self)

        # You're subtracting everything?
        if other.is_full_file():
            return TestRun.empty()

        def return_inclusions_or_empty(inclusions: frozenset[str]) -> TestRun:
            if inclusions:
                return TestRun(self.test_file, included=inclusions)
            return TestRun.empty()

        if other._included:
            if self._included:
                return return_inclusions_or_empty(self._included - other._included)
            else:
                return TestRun(
                    self.test_file, excluded=self._excluded | other._included
                )
        else:
            if self._included:
                return return_inclusions_or_empty(self._included & other._excluded)
            else:
                return return_inclusions_or_empty(other._excluded - self._excluded)