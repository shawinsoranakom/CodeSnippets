def test_recipients_with_empty_strings(self):
        """
        Empty strings in various recipient arguments are always stripped
        off the final recipient list.
        """
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com", ""],
            cc=["cc@example.com", ""],
            bcc=["", "bcc@example.com"],
            reply_to=["", None],
        )
        self.assertEqual(
            email.recipients(), ["to@example.com", "cc@example.com", "bcc@example.com"]
        )