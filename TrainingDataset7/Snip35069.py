def test_durations(self):
        with captured_stderr() as stderr:
            call_command(
                "test",
                "--durations=10",
                "sites",
                testrunner="test_runner.tests.MockTestRunner",
            )
        self.assertIn("durations=10", stderr.getvalue())