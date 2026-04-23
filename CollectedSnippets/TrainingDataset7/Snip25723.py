def test_custom_log_level(self):
        response = HttpResponse(status=403)
        with self.assertLogs("django.request", level="DEBUG") as cm:
            log_response(
                msg := "Debug level log",
                response=response,
                request=self.request,
                level="debug",
            )
        self.assertLogRecord(cm, msg, logging.DEBUG, 403, self.request)