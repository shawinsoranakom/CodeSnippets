def test_number_of_databases_no_parallel_test_suite(self):
        """
        Number of databases doesn't exceed the number of TestCases with
        non-parallel tests.
        """
        runner = DiscoverRunner(parallel=8, verbosity=0)
        suite = runner.build_suite(["test_runner_apps.simple.tests.DjangoCase1"])
        self.assertEqual(runner.parallel, 1)
        self.assertIsInstance(suite, TestSuite)