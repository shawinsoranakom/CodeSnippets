def test_number_of_parallel_workers(self):
        """Number of processes doesn't exceed the number of TestCases."""
        runner = DiscoverRunner(parallel=5, verbosity=0)
        suite = runner.build_suite(["test_runner_apps.tagged"])
        self.assertEqual(suite.processes, len(suite.subsuites))