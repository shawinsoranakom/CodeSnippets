def test_bcc_not_in_headers(self):
        """
        A bcc address should be in the recipients,
        but not in the (visible) message headers.
        """
        email = EmailMessage(
            to=["to@example.com"],
            bcc=["bcc@example.com"],
        )
        message = email.message()
        self.assertNotIn("Bcc", message)
        self.assertNotIn("bcc@example.com", message.as_string())
        self.assertEqual(email.recipients(), ["to@example.com", "bcc@example.com"])