def test_run_cleanup(self, _pre_setup, _post_teardown):
        """Simple test run: catches errors and runs cleanup."""
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("raising_test"))
        result = self.get_runner()._makeResult()
        self.assertEqual(result.errors, [])
        test_suite.run(result)
        self.assertEqual(len(result.errors), 1)
        _, traceback = result.errors[0]
        self.assertIn(
            "Exception: debug() bubbles up exceptions before cleanup.", traceback
        )
        _pre_setup.assert_called_once_with()
        _post_teardown.assert_called_once_with()