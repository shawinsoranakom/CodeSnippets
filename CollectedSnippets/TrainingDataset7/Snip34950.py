def test_discovery_on_package(self):
        count = (
            DiscoverRunner(verbosity=0)
            .build_suite(
                ["test_runner_apps.sample.tests"],
            )
            .countTestCases()
        )

        self.assertEqual(count, 1)