def test_reason_phrase(self):
        reason = "I'm an anarchist coffee pot on crack."
        resp = HttpResponse(status=419, reason=reason)
        self.assertEqual(resp.status_code, 419)
        self.assertEqual(resp.reason_phrase, reason)