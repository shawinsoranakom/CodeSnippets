def test_response_logged(self):
        with self.assertLogs("django.security.SuspiciousOperation", "ERROR") as handler:
            response = self.client.get("/suspicious/")

        self.assertLogRecord(
            handler, "dubious", logging.ERROR, 400, request=response.wsgi_request
        )
        self.assertEqual(response.status_code, 400)