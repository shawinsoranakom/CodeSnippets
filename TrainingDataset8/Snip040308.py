def test_healthcheck_responsibilities(self):
        response = self.fetch("/st-allowed-message-origins")
        self.assertEqual(200, response.code)

        self._is_healthy = False
        response = self.fetch("/st-allowed-message-origins")
        self.assertEqual(503, response.code)