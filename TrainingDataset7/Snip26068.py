def test_admin_receivers(self):
        """
        The mail should be sent to the email addresses specified in
        settings.ADMIN.
        """
        call_command("sendtestemail", "--admins")
        self.assertEqual(len(mail.outbox), 1)
        mail_message = mail.outbox[0]
        self.assertEqual(
            sorted(mail_message.recipients()),
            [
                "admin@example.com",
                "admin_and_manager@example.com",
            ],
        )