def split_tests(self, test_folder: TestFolder) -> None:
        """Split tests into buckets."""
        digits = len(str(test_folder.total_tests))
        sorted_tests = sorted(
            test_folder.get_all_flatten(), reverse=True, key=lambda x: x.total_tests
        )
        for tests in sorted_tests:
            if tests.added_to_bucket:
                # Already added to bucket
                continue

            print(f"{tests.total_tests:>{digits}} tests in {tests.path}")
            smallest_bucket = min(self._buckets, key=lambda x: x.total_tests)
            is_file = isinstance(tests, TestFile)
            if (
                smallest_bucket.total_tests + tests.total_tests < self._tests_per_bucket
            ) or is_file:
                smallest_bucket.add(tests)
                # Ensure all files from the same folder are in the same bucket
                # to ensure that syrupy correctly identifies unused snapshots
                if is_file:
                    for other_test in tests.parent.children.values():
                        if other_test is tests or isinstance(other_test, TestFolder):
                            continue
                        print(
                            f"{other_test.total_tests:>{digits}} tests in {other_test.path} (same bucket)"
                        )
                        smallest_bucket.add(other_test)

        # verify that all tests are added to a bucket
        if not test_folder.added_to_bucket:
            raise ValueError("Not all tests are added to a bucket")