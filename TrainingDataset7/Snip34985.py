def test_suite_result_with_failure(self):
        cases = [
            (1, "FailureTestCase"),
            (1, "ErrorTestCase"),
            (0, "ExpectedFailureTestCase"),
            (1, "UnexpectedSuccessTestCase"),
        ]
        runner = DiscoverRunner(verbosity=0)
        for expected_failures, testcase in cases:
            with self.subTest(testcase=testcase):
                suite = runner.build_suite(
                    [
                        f"test_runner_apps.failures.tests_failures.{testcase}",
                    ]
                )
                with captured_stderr():
                    result = runner.run_suite(suite)
                failures = runner.suite_result(suite, result)
                self.assertEqual(failures, expected_failures)