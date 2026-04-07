def test_method_frames_ignored_by_unittest(self):
        try:
            self.assertJSONEqual("1", "2")
        except AssertionError:
            exc_type, exc, tb = sys.exc_info()

        result = unittest.TestResult()
        result.addFailure(self, (exc_type, exc, tb))
        stack = traceback.extract_tb(exc.__traceback__)
        self.assertEqual(len(stack), 1)
        # Top element in the stack is this method, not assertJSONEqual.
        self.assertEqual(stack[-1].name, "test_method_frames_ignored_by_unittest")