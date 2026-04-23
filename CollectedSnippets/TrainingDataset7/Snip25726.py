def test_format_args_are_applied(self):
        response = HttpResponse(status=500)
        with self.assertLogs("django.request", level="ERROR") as cm:
            log_response(
                "Something went wrong: %s (%d)",
                "DB error",
                42,
                response=response,
                request=self.request,
            )
        msg = "Something went wrong: DB error (42)"
        self.assertLogRecord(cm, msg, logging.ERROR, 500, self.request)