def test_exclude_tags(self):
        runner = DiscoverRunner(tags=["fast"], exclude_tags=["core"], verbosity=0)
        self.assertEqual(
            runner.build_suite(["test_runner_apps.tagged.tests"]).countTestCases(), 1
        )
        runner = DiscoverRunner(tags=["fast"], exclude_tags=["slow"], verbosity=0)
        self.assertEqual(
            runner.build_suite(["test_runner_apps.tagged.tests"]).countTestCases(), 0
        )
        runner = DiscoverRunner(exclude_tags=["slow"], verbosity=0)
        self.assertEqual(
            runner.build_suite(["test_runner_apps.tagged.tests"]).countTestCases(), 0
        )