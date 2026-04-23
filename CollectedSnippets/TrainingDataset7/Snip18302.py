def test_email_found(self):
        "Email is sent if a valid email address is provided for password reset"
        response = self.client.post(
            "/password_reset/", {"email": "staffmember@example.com"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("http://", mail.outbox[0].body)
        self.assertEqual(settings.DEFAULT_FROM_EMAIL, mail.outbox[0].from_email)
        # optional multipart text/html email has been added. Make sure
        # original, default functionality is 100% the same
        self.assertFalse(mail.outbox[0].message().is_multipart())