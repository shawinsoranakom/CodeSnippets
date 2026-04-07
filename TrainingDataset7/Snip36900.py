def test_request_and_exception(self):
        "A simple exception report can be generated"
        try:
            request = self.rf.get("/test_view/")
            request.user = User()
            raise ValueError("Can't find my keys")
        except ValueError:
            exc_type, exc_value, tb = sys.exc_info()
        reporter = ExceptionReporter(request, exc_type, exc_value, tb)
        html = reporter.get_traceback_html()
        self.assertInHTML("<h1>ValueError at /test_view/</h1>", html)
        self.assertIn(
            '<pre class="exception_value">Can&#x27;t find my keys</pre>', html
        )
        self.assertIn('<th scope="row">Request Method:</th>', html)
        self.assertIn('<th scope="row">Request URL:</th>', html)
        self.assertIn('<h3 id="user-info">USER</h3>', html)
        self.assertIn("<p>jacob</p>", html)
        self.assertIn('<th scope="row">Exception Type:</th>', html)
        self.assertIn('<th scope="row">Exception Value:</th>', html)
        self.assertIn("<h2>Traceback ", html)
        self.assertIn("<h2>Request information</h2>", html)
        self.assertNotIn("<p>Request data not supplied</p>", html)
        self.assertIn("<p>No POST data</p>", html)