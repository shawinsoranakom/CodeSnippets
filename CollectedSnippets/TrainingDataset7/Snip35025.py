def test_handle_add_success(self):
        dummy_subsuites = []
        pts = ParallelTestSuite(dummy_subsuites, processes=2)
        result = TestResult()
        test = TestCase()
        event = ("addSuccess", 0)
        pts.handle_event(result, tests=[test], event=event)

        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.failures), 0)