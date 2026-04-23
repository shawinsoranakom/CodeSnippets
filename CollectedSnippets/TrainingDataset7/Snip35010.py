def test_was_successful_no_events(self):
        result = RemoteTestResult()
        self.assertIs(result.wasSuccessful(), True)