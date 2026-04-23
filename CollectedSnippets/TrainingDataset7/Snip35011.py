def test_was_successful_one_success(self):
        result = RemoteTestResult()
        test = None
        result.startTest(test)
        try:
            result.addSuccess(test)
        finally:
            result.stopTest(test)
        self.assertIs(result.wasSuccessful(), True)