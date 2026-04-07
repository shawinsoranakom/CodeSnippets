def test_number_of_databases_parallel_test_suite(self):
        """
        Number of databases doesn't exceed the number of TestCases with
        parallel tests.
        """
        runner = DiscoverRunner(parallel=8, verbosity=0)
        suite = runner.build_suite(["test_runner_apps.tagged"])
        self.assertEqual(suite.processes, len(suite.subsuites))
        self.assertEqual(runner.parallel, suite.processes)