def test_message_cc_header(self):
        """
        Regression test for #7722
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            cc=["cc@example.com"],
        )
        mail.get_connection().send_messages([email])
        message = self.get_the_message()
        self.assertMessageHasHeaders(
            message,
            {
                ("MIME-Version", "1.0"),
                ("Content-Type", 'text/plain; charset="utf-8"'),
                ("Content-Transfer-Encoding", "7bit"),
                ("Subject", "Subject"),
                ("From", "from@example.com"),
                ("To", "to@example.com"),
                ("Cc", "cc@example.com"),
            },
        )
        self.assertIn("\nDate: ", message.as_string())