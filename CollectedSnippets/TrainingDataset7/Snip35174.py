def test_debug_bubbles_post_teardown_error(self, _pre_setup, _post_teardown):
        """debug() bubbles up exceptions during _post_teardown."""
        msg = "Exception in _post_teardown."
        _post_teardown.side_effect = Exception(msg)
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("simple_test"))
        with self.assertRaisesMessage(Exception, msg):
            # This is the same as test_suite.debug().
            result = _DebugResult()
            test_suite.run(result, debug=True)
        # pre-setup and post-teardwn are called.
        _pre_setup.assert_called_once_with()
        _post_teardown.assert_called_once_with()
        self.isolate_debug_test(test_suite, result)