def test_ignore_adjacent(self):
        """
        When given a dotted path to a module, unittest discovery searches
        not just the module, but also the directory containing the module.

        This results in tests from adjacent modules being run when they
        should not. The discover runner avoids this behavior.
        """
        count = (
            DiscoverRunner(verbosity=0)
            .build_suite(
                ["test_runner_apps.sample.empty"],
            )
            .countTestCases()
        )

        self.assertEqual(count, 0)