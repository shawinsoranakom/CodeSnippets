def test_email_found_custom_from(self):
        """
        Email is sent if a valid email address is provided for password reset
        when a custom from_email is provided.
        """
        response = self.client.post(
            "/password_reset_from_email/", {"email": "staffmember@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual("staffmember@example.com", mail.outbox[0].from_email)