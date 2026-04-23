def test_handle_add_error_before_first_test(self):
        dummy_subsuites = []
        pts = ParallelTestSuite(dummy_subsuites, processes=2)
        result = TestResult()
        remote_result = RemoteTestResult()
        test = SampleErrorTest(methodName="dummy_test")
        suite = TestSuite([test])
        suite.run(remote_result)
        for event in remote_result.events:
            pts.handle_event(result, tests=list(suite), event=event)

        self.assertEqual(len(result.errors), 1)
        actual_test, tb_and_details_str = result.errors[0]
        self.assertIsInstance(actual_test, _ErrorHolder)
        self.assertEqual(
            actual_test.id(), "setUpClass (test_runner.test_parallel.SampleErrorTest)"
        )
        self.assertIn("Traceback (most recent call last):", tb_and_details_str)
        self.assertIn("ValueError: woops", tb_and_details_str)