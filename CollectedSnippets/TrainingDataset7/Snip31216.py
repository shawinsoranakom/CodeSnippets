def test_status_code(self):
        resp = HttpResponse(status=503)
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.reason_phrase, "Service Unavailable")