def test_logs_4xx_as_warning(self):
        response = HttpResponse(status=418)
        with self.assertLogs("django.request", level="WARNING") as cm:
            log_response(
                msg := "This is a teapot!", response=response, request=self.request
            )
        self.assertLogRecord(cm, msg, logging.WARNING, 418, self.request)