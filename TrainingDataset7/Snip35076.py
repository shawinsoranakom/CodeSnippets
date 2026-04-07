def test_django_test_processes_env_non_int(self, *mocked_objects):
        with self.assertRaises(ValueError):
            call_command(
                "test",
                "--parallel",
                testrunner="test_runner.tests.MockTestRunner",
            )