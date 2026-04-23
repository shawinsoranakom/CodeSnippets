def test_durations(self):
        with captured_stderr() as stderr, captured_stdout():
            runner = DiscoverRunner(durations=10)
            suite = runner.build_suite(["test_runner_apps.simple.tests.SimpleCase1"])
            runner.run_suite(suite)
        self.assertIn("Slowest test durations", stderr.getvalue())