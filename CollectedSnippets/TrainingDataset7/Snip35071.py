def test_parallel_auto(self, *mocked_objects):
        with captured_stderr() as stderr:
            call_command(
                "test",
                "--parallel=auto",
                testrunner="test_runner.tests.MockTestRunner",
            )
        self.assertIn("parallel=12", stderr.getvalue())