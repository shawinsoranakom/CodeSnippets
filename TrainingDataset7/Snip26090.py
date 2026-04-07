def test_recipients_as_tuple(self):
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ("to@example.com", "other@example.com"),
            cc=("cc@example.com", "cc.other@example.com"),
            bcc=("bcc@example.com",),
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com, cc.other@example.com")
        self.assertEqual(
            email.recipients(),
            [
                "to@example.com",
                "other@example.com",
                "cc@example.com",
                "cc.other@example.com",
                "bcc@example.com",
            ],
        )