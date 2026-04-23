def _test_confirm_start(self):
        # Start by creating the email
        response = self.client.post("/password_reset/", {"email": self.user_email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        return self._read_signup_email(mail.outbox[0])