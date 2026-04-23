def test_no_initialize_suite_test_runner(self, *mocked_objects):
        """
        The test suite's initialize_suite() method must always be called when
        using spawn. It cannot rely on a test runner implementation.
        """

        class NoInitializeSuiteTestRunner(DiscoverRunner):
            def setup_test_environment(self, **kwargs):
                return

            def setup_databases(self, **kwargs):
                return

            def run_checks(self, databases):
                return

            def teardown_databases(self, old_config, **kwargs):
                return

            def teardown_test_environment(self, **kwargs):
                return

            def run_suite(self, suite, **kwargs):
                kwargs = self.get_test_runner_kwargs()
                runner = self.test_runner(**kwargs)
                return runner.run(suite)

        with self.assertRaisesMessage(Exception, "initialize_suite() is called."):
            runner = NoInitializeSuiteTestRunner(
                verbosity=0, interactive=False, parallel=2
            )
            runner.run_tests(
                [
                    "test_runner_apps.sample.tests_sample.TestDjangoTestCase",
                    "test_runner_apps.simple.tests",
                ]
            )