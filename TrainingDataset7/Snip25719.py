def test_missing_request_logs_with_none(self):
        response = HttpResponse(status=403)
        with self.assertLogs("django.request", level="INFO") as cm:
            log_response(msg := "Missing request", response=response, request=None)
        self.assertLogRecord(cm, msg, logging.WARNING, 403, request=None)