def test_send_unicode(self):
        email = EmailMessage(
            "Chère maman",
            "Je t'aime très fort\n",
            "from@example.com",
            ["to@example.com"],
        )
        num_sent = mail.get_connection().send_messages([email])
        self.assertEqual(num_sent, 1)
        message = self.get_the_message()
        self.assertEqual(message["subject"], "Chère maman")
        self.assertEqual(message.get_content(), "Je t'aime très fort\n")