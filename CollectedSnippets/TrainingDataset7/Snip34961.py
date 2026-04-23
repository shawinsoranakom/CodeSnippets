def test_tags(self):
        runner = DiscoverRunner(tags=["core"], verbosity=0)
        self.assertEqual(
            runner.build_suite(["test_runner_apps.tagged.tests"]).countTestCases(), 1
        )
        runner = DiscoverRunner(tags=["fast"], verbosity=0)
        self.assertEqual(
            runner.build_suite(["test_runner_apps.tagged.tests"]).countTestCases(), 2
        )
        runner = DiscoverRunner(tags=["slow"], verbosity=0)
        self.assertEqual(
            runner.build_suite(["test_runner_apps.tagged.tests"]).countTestCases(), 2
        )