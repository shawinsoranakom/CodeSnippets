def test_was_successful_one_error(self):
        result = RemoteTestResult()
        test = None
        result.startTest(test)
        try:
            result.addError(test, _test_error_exc_info())
        finally:
            result.stopTest(test)
        self.assertIs(result.wasSuccessful(), False)