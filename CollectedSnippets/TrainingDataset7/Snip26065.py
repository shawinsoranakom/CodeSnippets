def test_multiple_receivers(self):
        """
        The mail may be sent with multiple recipients.
        """
        recipients = ["joe@example.com", "jane@example.com"]
        call_command("sendtestemail", recipients[0], recipients[1])
        self.assertEqual(len(mail.outbox), 1)
        mail_message = mail.outbox[0]
        self.assertEqual(mail_message.subject[0:15], "Test email from")
        self.assertEqual(
            sorted(mail_message.recipients()),
            [
                "jane@example.com",
                "joe@example.com",
            ],
        )