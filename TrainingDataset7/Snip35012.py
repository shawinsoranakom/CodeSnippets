def test_was_successful_one_expected_failure(self):
        result = RemoteTestResult()
        test = None
        result.startTest(test)
        try:
            result.addExpectedFailure(test, _test_error_exc_info())
        finally:
            result.stopTest(test)
        self.assertIs(result.wasSuccessful(), True)