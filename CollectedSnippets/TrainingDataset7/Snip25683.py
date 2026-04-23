def test_uncaught_exception(self):
        self.assertLogsRequest(
            url="/uncaught_exception/",
            level="ERROR",
            status_code=500,
            msg="Internal Server Error: /uncaught_exception/",
            exc_class=views.UncaughtException,
        )