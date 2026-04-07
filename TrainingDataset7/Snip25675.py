def assertLogsRequest(
        self, url, level, msg, status_code, logger="django.request", exc_class=None
    ):
        with self.assertLogs(logger, level) as cm:
            try:
                self.client.get(url)
            except views.UncaughtException:
                pass
            self.assertLogRecord(
                cm, msg, getattr(logging, level), status_code, exc_class=exc_class
            )