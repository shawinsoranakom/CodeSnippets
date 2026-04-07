def test_no_parallel_spawn(self, *mocked_objects):
        with captured_stderr() as stderr:
            call_command(
                "test",
                testrunner="test_runner.tests.MockTestRunner",
            )
        self.assertEqual(stderr.getvalue(), "")