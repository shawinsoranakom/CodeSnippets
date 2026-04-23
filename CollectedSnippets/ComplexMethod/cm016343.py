def __or__(self, other: TestRun) -> TestRun:
        """
        To OR/Union test runs means to run all the tests that either of the two runs specify.
        """

        # Is any file empty?
        if self.is_empty():
            return other
        if other.is_empty():
            return copy(self)

        # If not, ensure we have the same file
        if self.test_file != other.test_file:
            raise AssertionError(
                f"Can't exclude {other} from {self} because they're not the same test file"
            )

        # 4 possible cases:

        # 1. Either file is the full file, so union is everything
        if self.is_full_file() or other.is_full_file():
            # The union is the whole file
            return TestRun(self.test_file)

        # 2. Both files only run what's in _included, so union is the union of the two sets
        if self._included and other._included:
            return TestRun(
                self.test_file, included=self._included.union(other._included)
            )

        # 3. Both files only exclude what's in _excluded, so union is the intersection of the two sets
        if self._excluded and other._excluded:
            return TestRun(
                self.test_file, excluded=self._excluded.intersection(other._excluded)
            )

        # 4. One file includes and the other excludes, so we then continue excluding the _excluded set minus
        #    whatever is in the _included set
        included = self._included | other._included
        excluded = self._excluded | other._excluded
        return TestRun(self.test_file, excluded=excluded - included)