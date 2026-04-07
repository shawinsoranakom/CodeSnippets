def test_run_post_teardown_error(self, _pre_setup, _post_teardown):
        _post_teardown.side_effect = Exception("Exception in _post_teardown.")
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("simple_test"))
        result = self.get_runner()._makeResult()
        self.assertEqual(result.errors, [])
        test_suite.run(result)
        self.assertEqual(len(result.errors), 1)
        _, traceback = result.errors[0]
        self.assertIn("Exception: Exception in _post_teardown.", traceback)
        # pre-setup and post-teardwn are called.
        _pre_setup.assert_called_once_with()
        _post_teardown.assert_called_once_with()