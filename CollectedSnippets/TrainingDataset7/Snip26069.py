def test_manager_and_admin_receivers(self):
        """
        The mail should be sent to the email addresses specified in both
        settings.MANAGERS and settings.ADMINS.
        """
        call_command("sendtestemail", "--managers", "--admins")
        self.assertEqual(len(mail.outbox), 2)
        manager_mail = mail.outbox[0]
        self.assertEqual(
            sorted(manager_mail.recipients()),
            [
                "admin_and_manager@example.com",
                "manager@example.com",
            ],
        )
        admin_mail = mail.outbox[1]
        self.assertEqual(
            sorted(admin_mail.recipients()),
            [
                "admin@example.com",
                "admin_and_manager@example.com",
            ],
        )