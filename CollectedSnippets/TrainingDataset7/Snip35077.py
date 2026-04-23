def test_django_test_processes_parallel_default(self, *mocked_objects):
        for parallel in ["--parallel", "--parallel=auto"]:
            with self.subTest(parallel=parallel):
                with captured_stderr() as stderr:
                    call_command(
                        "test",
                        parallel,
                        testrunner="test_runner.tests.MockTestRunner",
                    )
                self.assertIn("parallel=7", stderr.getvalue())