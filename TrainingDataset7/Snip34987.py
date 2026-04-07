def test_durations_debug_sql(self):
        with captured_stderr() as stderr, captured_stdout():
            runner = DiscoverRunner(durations=10, debug_sql=True)
            suite = runner.build_suite(["test_runner_apps.simple.SimpleCase1"])
            runner.run_suite(suite)
        self.assertIn("Slowest test durations", stderr.getvalue())