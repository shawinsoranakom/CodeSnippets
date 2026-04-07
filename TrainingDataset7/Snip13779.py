def build_suite(self, test_labels=None, **kwargs):
        test_labels = test_labels or ["."]

        discover_kwargs = {}
        if self.pattern is not None:
            discover_kwargs["pattern"] = self.pattern
        if self.top_level is not None:
            discover_kwargs["top_level_dir"] = self.top_level
        self.setup_shuffler()

        all_tests = []
        for label in test_labels:
            tests = self.load_tests_for_label(label, discover_kwargs)
            all_tests.extend(iter_test_cases(tests))

        if self.tags or self.exclude_tags:
            if self.tags:
                self.log(
                    "Including test tag(s): %s." % ", ".join(sorted(self.tags)),
                    level=logging.DEBUG,
                )
            if self.exclude_tags:
                self.log(
                    "Excluding test tag(s): %s." % ", ".join(sorted(self.exclude_tags)),
                    level=logging.DEBUG,
                )
            all_tests = filter_tests_by_tags(all_tests, self.tags, self.exclude_tags)

        # Put the failures detected at load time first for quicker feedback.
        # _FailedTest objects include things like test modules that couldn't be
        # found or that couldn't be loaded due to syntax errors.
        test_types = (unittest.loader._FailedTest, *self.reorder_by)
        all_tests = list(
            reorder_tests(
                all_tests,
                test_types,
                shuffler=self._shuffler,
                reverse=self.reverse,
            )
        )
        self.log("Found %d test(s)." % len(all_tests))
        suite = self.test_suite(all_tests)

        if self.parallel > 1:
            subsuites = partition_suite_by_case(suite)
            # Since tests are distributed across processes on a per-TestCase
            # basis, there's no need for more processes than TestCases.
            processes = min(self.parallel, len(subsuites))
            # Update also "parallel" because it's used to determine the number
            # of test databases.
            self.parallel = processes
            if processes > 1:
                suite = self.parallel_test_suite(
                    subsuites,
                    processes,
                    self.failfast,
                    self.debug_mode,
                    self.buffer,
                )
        return suite