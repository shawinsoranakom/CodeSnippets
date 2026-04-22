def test_allowed_message_origins(self):
        response = self.fetch("/st-allowed-message-origins")
        self.assertEqual(200, response.code)
        self.assertEqual(
            {"allowedOrigins": ALLOWED_MESSAGE_ORIGINS}, json.loads(response.body)
        )