def test_buffer_mode_test_pass(self):
        runner = DiscoverRunner(buffer=True, verbosity=0)
        with captured_stdout() as stdout, captured_stderr() as stderr:
            suite = runner.build_suite(
                [
                    "test_runner_apps.buffer.tests_buffer.WriteToStdoutStderrTestCase."
                    "test_pass",
                ]
            )
            runner.run_suite(suite)
        self.assertNotIn("Write to stderr.", stderr.getvalue())
        self.assertNotIn("Write to stdout.", stdout.getvalue())