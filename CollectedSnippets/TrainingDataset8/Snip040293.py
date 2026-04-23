def test_healthz(self):
        response = self.fetch("/healthz")
        self.assertEqual(200, response.code)
        self.assertEqual(b"ok", response.body)

        self._is_healthy = False
        response = self.fetch("/healthz")
        self.assertEqual(503, response.code)