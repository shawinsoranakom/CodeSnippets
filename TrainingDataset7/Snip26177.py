def test_email_multi_alternatives_init(self):
        with self.assertDeprecatedIn70(
            "'bcc', 'connection', 'attachments', 'headers', 'alternatives', 'cc', "
            "'reply_to'",
            "EmailMultiAlternatives",
        ):
            EmailMultiAlternatives(
                "subject",
                "body\n",
                "from@example.com",
                ["to@example.com"],
                # Deprecated positional args:
                ["bcc@example.com"],
                mail.get_connection(),
                [EmailAttachment("file.txt", "attachment\n", "text/plain")],
                {"X-Header": "custom header"},
                [EmailAlternative("html body", "text/html")],
                ["cc@example.com"],
                ["reply-to@example.com"],
            )