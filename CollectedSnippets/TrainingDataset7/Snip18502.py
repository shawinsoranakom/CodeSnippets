def test_mark_expected_failures_and_skips(self):
        test_connection = get_connection_copy()
        creation = BaseDatabaseCreation(test_connection)
        creation.connection.features.django_test_expected_failures = {
            "backends.base.test_creation.expected_failure_test_function",
        }
        creation.connection.features.django_test_skips = {
            "skip test class": {
                "backends.base.test_creation.SkipTestClass",
            },
            "skip test function": {
                "backends.base.test_creation.skip_test_function",
            },
        }
        # Emulate the scenario where the parent module for
        # backends.base.test_creation has not been imported yet.
        popped_module = sys.modules.pop("backends.base")
        self.addCleanup(sys.modules.__setitem__, "backends.base", popped_module)
        creation.mark_expected_failures_and_skips()
        self.assertIs(
            expected_failure_test_function.__unittest_expecting_failure__,
            True,
        )
        self.assertIs(SkipTestClass.__unittest_skip__, True)
        self.assertEqual(
            SkipTestClass.__unittest_skip_why__,
            "skip test class",
        )
        self.assertIs(skip_test_function.__unittest_skip__, True)
        self.assertEqual(
            skip_test_function.__unittest_skip_why__,
            "skip test function",
        )