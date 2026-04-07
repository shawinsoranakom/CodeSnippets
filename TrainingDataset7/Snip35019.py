def test_unpicklable_subtest(self):
        result = RemoteTestResult()
        subtest_test = SampleFailingSubtest(methodName="pickle_error_test")
        subtest_test.run(result=result)

        events = result.events
        subtest_event = events[1]
        assertion_error = subtest_event[3]
        self.assertEqual(str(assertion_error[1]), "expected failure")