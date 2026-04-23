def _test_confirm_start(self):
        # Start by creating the email
        self.client.post("/password_reset/", {"email": "staffmember@example.com"})
        self.assertEqual(len(mail.outbox), 1)
        return self._read_signup_email(mail.outbox[0])