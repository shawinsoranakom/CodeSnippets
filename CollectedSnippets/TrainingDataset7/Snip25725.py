def test_exc_info_output(self):
        response = HttpResponse(status=500)
        try:
            raise ValueError("Simulated failure")
        except ValueError as exc:
            with self.assertLogs("django.request", level="ERROR") as cm:
                log_response(
                    "With exception",
                    response=response,
                    request=self.request,
                    exception=exc,
                )
        self.assertLogRecord(cm, "With exception", logging.ERROR, 500, self.request)
        self.assertIn("ValueError", "\n".join(cm.output))