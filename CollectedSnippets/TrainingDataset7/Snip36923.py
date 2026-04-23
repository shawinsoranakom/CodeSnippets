def test_disallowed_host(self):
        "An exception report can be generated even for a disallowed host."
        request = self.rf.get("/", headers={"host": "evil.com"})
        reporter = ExceptionReporter(request, None, None, None)
        html = reporter.get_traceback_html()
        self.assertIn("http://evil.com/", html)