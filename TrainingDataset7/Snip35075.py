def test_no_parallel_django_test_processes_env(self, *mocked_objects):
        with captured_stderr() as stderr:
            call_command("test", testrunner="test_runner.tests.MockTestRunner")
        self.assertEqual(stderr.getvalue(), "")