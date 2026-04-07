def test_picklable(self):
        result = RemoteTestResult()
        loaded_result = pickle.loads(pickle.dumps(result))
        self.assertEqual(result.events, loaded_result.events)