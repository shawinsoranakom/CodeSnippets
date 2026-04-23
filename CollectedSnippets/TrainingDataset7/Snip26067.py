def test_manager_receivers(self):
        """
        The mail should be sent to the email addresses specified in
        settings.MANAGERS.
        """
        call_command("sendtestemail", "--managers")
        self.assertEqual(len(mail.outbox), 1)
        mail_message = mail.outbox[0]
        self.assertEqual(
            sorted(mail_message.recipients()),
            [
                "admin_and_manager@example.com",
                "manager@example.com",
            ],
        )