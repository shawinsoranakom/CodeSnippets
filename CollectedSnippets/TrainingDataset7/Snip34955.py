def test_build_suite_failed_tests_first(self):
        # The "doesnotexist" label results in a _FailedTest instance.
        suite = DiscoverRunner(verbosity=0).build_suite(
            test_labels=["test_runner_apps.sample", "doesnotexist"],
        )
        tests = list(suite)
        self.assertIsInstance(tests[0], unittest.loader._FailedTest)
        self.assertNotIsInstance(tests[-1], unittest.loader._FailedTest)