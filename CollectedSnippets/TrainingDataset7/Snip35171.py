def test_debug_cleanup(self, _pre_setup, _post_teardown):
        """Simple debug run without errors."""
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("simple_test"))
        test_suite.debug()
        _pre_setup.assert_called_once_with()
        _post_teardown.assert_called_once_with()