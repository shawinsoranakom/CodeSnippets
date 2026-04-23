def test_healthcheck_responsibilities_without_csrf(self):
        response = self.fetch("/st-allowed-message-origins")
        self.assertEqual(200, response.code)
        self.assertNotIn("Set-Cookie", response.headers)