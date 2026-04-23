def test_email_message_init(self):
        with self.assertDeprecatedIn70(
            "'bcc', 'connection', 'attachments', 'headers', 'cc', 'reply_to'",
            "EmailMessage",
        ):
            EmailMessage(
                "subject",
                "body\n",
                "from@example.com",
                ["to@example.com"],
                # Deprecated positional args:
                ["bcc@example.com"],
                mail.get_connection(),
                [EmailAttachment("file.txt", "attachment\n", "text/plain")],
                {"X-Header": "custom header"},
                ["cc@example.com"],
                ["reply-to@example.com"],
            )