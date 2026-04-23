def test_suspicious_operation_uses_sublogger(self):
        self.assertLogsRequest(
            url="/suspicious_spec/",
            level="ERROR",
            msg="dubious",
            status_code=400,
            logger="django.security.DisallowedHost",
            exc_class=DisallowedHost,
        )