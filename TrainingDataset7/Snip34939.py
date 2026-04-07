def test_dotted_test_module(self):
        count = (
            DiscoverRunner(verbosity=0)
            .build_suite(
                ["test_runner_apps.sample.tests_sample"],
            )
            .countTestCases()
        )

        self.assertEqual(count, 4)