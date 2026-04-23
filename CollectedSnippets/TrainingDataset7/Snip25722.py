def test_logs_2xx_as_info(self):
        response = HttpResponse(status=201)
        with self.assertLogs("django.request", level="INFO") as cm:
            log_response(msg := "OK response", response=response, request=self.request)
        self.assertLogRecord(cm, msg, logging.INFO, 201, self.request)