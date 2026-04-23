def test_handle_add_error_during_test(self):
        dummy_subsuites = []
        pts = ParallelTestSuite(dummy_subsuites, processes=2)
        result = TestResult()
        test = TestCase()
        err = _test_error_exc_info()
        event = ("addError", 0, err)
        pts.handle_event(result, tests=[test], event=event)

        self.assertEqual(len(result.errors), 1)
        actual_test, tb_and_details_str = result.errors[0]
        self.assertIsInstance(actual_test, TestCase)
        self.assertEqual(actual_test.id(), "unittest.case.TestCase.runTest")
        self.assertIn("Traceback (most recent call last):", tb_and_details_str)
        self.assertIn("ValueError: woops", tb_and_details_str)