def test_run_pre_setup_error(self, _pre_setup, _post_teardown):
        _pre_setup.side_effect = Exception("Exception in _pre_setup.")
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("simple_test"))
        result = self.get_runner()._makeResult()
        self.assertEqual(result.errors, [])
        test_suite.run(result)
        self.assertEqual(len(result.errors), 1)
        _, traceback = result.errors[0]
        self.assertIn("Exception: Exception in _pre_setup.", traceback)
        # pre-setup is called but not post-teardown.
        _pre_setup.assert_called_once_with()
        self.assertFalse(_post_teardown.called)