def test_healthcheck_responsibilities_with_csrf(self):
        response = self.fetch("/st-allowed-message-origins")
        self.assertEqual(200, response.code)
        self.assertIn("Set-Cookie", response.headers)