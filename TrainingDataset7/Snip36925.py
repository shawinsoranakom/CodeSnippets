def test_exception_fetching_user(self):
        """
        The error page can be rendered if the current user can't be retrieved
        (such as when the database is unavailable).
        """

        class ExceptionUser:
            def __str__(self):
                raise Exception()

        request = self.rf.get("/test_view/")
        request.user = ExceptionUser()

        try:
            raise ValueError("Oops")
        except ValueError:
            exc_type, exc_value, tb = sys.exc_info()

        reporter = ExceptionReporter(request, exc_type, exc_value, tb)
        html = reporter.get_traceback_html()
        self.assertInHTML("<h1>ValueError at /test_view/</h1>", html)
        self.assertIn('<pre class="exception_value">Oops</pre>', html)
        self.assertIn('<h3 id="user-info">USER</h3>', html)
        self.assertIn("<p>[unable to retrieve the current user]</p>", html)

        text = reporter.get_traceback_text()
        self.assertIn("USER: [unable to retrieve the current user]", text)