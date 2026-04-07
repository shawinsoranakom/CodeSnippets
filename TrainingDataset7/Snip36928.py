def test_request_and_exception(self):
        "A simple exception report can be generated"
        try:
            request = self.rf.get("/test_view/")
            request.user = User()
            raise ValueError("Can't find my keys")
        except ValueError:
            exc_type, exc_value, tb = sys.exc_info()
        reporter = ExceptionReporter(request, exc_type, exc_value, tb)
        text = reporter.get_traceback_text()
        self.assertIn("ValueError at /test_view/", text)
        self.assertIn("Can't find my keys", text)
        self.assertIn("Request Method:", text)
        self.assertIn("Request URL:", text)
        self.assertIn("USER: jacob", text)
        self.assertIn("Exception Type:", text)
        self.assertIn("Exception Value:", text)
        self.assertIn("Traceback (most recent call last):", text)
        self.assertIn("Request information:", text)
        self.assertNotIn("Request data not supplied", text)