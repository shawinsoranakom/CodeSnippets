def test_was_successful_one_skip(self):
        result = RemoteTestResult()
        test = None
        result.startTest(test)
        try:
            result.addSkip(test, "Skipped")
        finally:
            result.stopTest(test)
        self.assertIs(result.wasSuccessful(), True)