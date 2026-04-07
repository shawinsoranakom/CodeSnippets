def test_multiple_recipients(self):
        email = EmailMessage(
            "Subject",
            "Content\n",
            "from@example.com",
            ["to@example.com", "other@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Subject"], "Subject")
        self.assertEqual(message.get_payload(), "Content\n")
        self.assertEqual(message["From"], "from@example.com")
        self.assertEqual(message["To"], "to@example.com, other@example.com")