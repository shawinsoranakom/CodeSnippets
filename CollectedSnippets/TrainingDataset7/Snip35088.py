def test_no_initialize_suite_test_runner(self, mocked_pool):
        class StubTestRunner(DiscoverRunner):
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

        runner = StubTestRunner(
            verbosity=0, interactive=False, parallel=2, debug_mode=True
        )
        with self.assertRaisesMessage(Exception, "multiprocessing.Pool()"):
            runner.run_tests(
                [
                    "test_runner_apps.sample.tests_sample.TestDjangoTestCase",
                    "test_runner_apps.simple.tests",
                ]
            )
        # Initializer must be a partial function binding _init_worker.
        initializer = mocked_pool.call_args.kwargs["initializer"]
        self.assertIsInstance(initializer, functools.partial)
        self.assertIs(initializer.args[0], _init_worker)
        initargs = mocked_pool.call_args.kwargs["initargs"]
        self.assertEqual(len(initargs), 7)
        self.assertEqual(initargs[5], True)  # debug_mode
        self.assertEqual(initargs[6], {db.DEFAULT_DB_ALIAS})