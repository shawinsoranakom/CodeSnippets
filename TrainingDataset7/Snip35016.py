def test_add_error_before_first_test(self):
        result = RemoteTestResult()
        test_id = "test_foo (tests.test_foo.FooTest.test_foo)"
        test = _ErrorHolder(test_id)
        # Call addError() without a call to startTest().
        result.addError(test, _test_error_exc_info())

        (event,) = result.events
        self.assertEqual(event[0], "addError")
        self.assertEqual(event[1], -1)
        self.assertEqual(event[2], test_id)
        error_type, _, _ = event[3]
        self.assertEqual(error_type, ValueError)
        self.assertIs(result.wasSuccessful(), False)