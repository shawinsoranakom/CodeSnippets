def test_extra_email_context(self):
        """
        extra_email_context should be available in the email template context.
        """
        response = self.client.post(
            "/password_reset_extra_email_context/",
            {"email": "staffmember@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Email email context: "Hello!"', mail.outbox[0].body)
        self.assertIn("http://custom.example.com/reset/", mail.outbox[0].body)