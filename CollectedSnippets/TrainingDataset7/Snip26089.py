def test_reply_to(self):
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            reply_to=["reply_to@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Reply-To"], "reply_to@example.com")

        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            reply_to=["reply_to1@example.com", "reply_to2@example.com"],
        )
        message = email.message()
        self.assertEqual(
            message["Reply-To"], "reply_to1@example.com, reply_to2@example.com"
        )