def test_pattern(self):
        count = (
            DiscoverRunner(
                pattern="*_tests.py",
                verbosity=0,
            )
            .build_suite(["test_runner_apps.sample"])
            .countTestCases()
        )

        self.assertEqual(count, 1)