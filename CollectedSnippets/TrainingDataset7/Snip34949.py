def test_empty_test_case(self):
        count = (
            DiscoverRunner(verbosity=0)
            .build_suite(
                ["test_runner_apps.sample.tests_sample.EmptyTestCase"],
            )
            .countTestCases()
        )

        self.assertEqual(count, 0)