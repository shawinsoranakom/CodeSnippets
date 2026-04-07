def test_logs_5xx_as_error(self):
        response = HttpResponse(status=508)
        with self.assertLogs("django.request", level="ERROR") as cm:
            log_response(
                msg := "Server error occurred", response=response, request=self.request
            )
        self.assertLogRecord(cm, msg, logging.ERROR, 508, self.request)