def test_run_skipped_test_no_cleanup(self, _pre_setup, _post_teardown):
        test_suite = unittest.TestSuite()
        test_suite.addTest(ErrorTestCase("skipped_test"))
        try:
            test_suite.run(self.get_runner()._makeResult())
        except unittest.SkipTest:
            self.fail("SkipTest should not be raised at this stage.")
        self.assertFalse(_post_teardown.called)
        self.assertFalse(_pre_setup.called)