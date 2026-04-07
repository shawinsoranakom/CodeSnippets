def test_suspicious_operation_creates_log_message(self):
        self.assertLogsRequest(
            url="/suspicious/",
            level="ERROR",
            msg="dubious",
            status_code=400,
            logger="django.security.SuspiciousOperation",
            exc_class=SuspiciousOperation,
        )