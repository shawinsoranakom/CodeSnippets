def test_logs_only_once_per_response(self):
        response = HttpResponse(status=500)
        with self.assertLogs("django.request", level="ERROR") as cm:
            log_response("First log", response=response, request=self.request)
            log_response("Second log", response=response, request=self.request)
        self.assertLogRecord(cm, "First log", logging.ERROR, 500, self.request)