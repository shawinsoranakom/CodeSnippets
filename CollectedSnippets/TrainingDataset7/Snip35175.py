def test_debug_skipped_test_no_cleanup(self, _pre_setup, _post_teardown):
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("skipped_test"))
        with self.assertRaisesMessage(unittest.SkipTest, "Skip condition."):
            # This is the same as test_suite.debug().
            result = _DebugResult()
            test_suite.run(result, debug=True)
        self.assertFalse(_post_teardown.called)
        self.assertFalse(_pre_setup.called)
        self.isolate_debug_test(test_suite, result)