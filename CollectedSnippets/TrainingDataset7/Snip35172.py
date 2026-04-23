def test_debug_bubbles_error(self, _pre_setup, _post_teardown):
        """debug() bubbles up exceptions before cleanup."""
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("raising_test"))
        msg = "debug() bubbles up exceptions before cleanup."
        with self.assertRaisesMessage(Exception, msg):
            # This is the same as test_suite.debug().
            result = _DebugResult()
            test_suite.run(result, debug=True)
        # pre-setup is called but not post-teardown.
        _pre_setup.assert_called_once_with()
        self.assertFalse(_post_teardown.called)
        self.isolate_debug_test(test_suite, result)