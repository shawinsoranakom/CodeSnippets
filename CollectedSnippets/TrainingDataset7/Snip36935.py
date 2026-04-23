def test_disallowed_host(self):
        "An exception report can be generated even for a disallowed host."
        request = self.rf.get("/", headers={"host": "evil.com"})
        reporter = ExceptionReporter(request, None, None, None)
        text = reporter.get_traceback_text()
        self.assertIn("http://evil.com/", text)