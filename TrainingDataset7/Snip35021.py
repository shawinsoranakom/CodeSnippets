def test_add_duration(self):
        result = RemoteTestResult()
        result.addDuration(None, 2.3)
        self.assertEqual(result.collectedDurations, [("None", 2.3)])