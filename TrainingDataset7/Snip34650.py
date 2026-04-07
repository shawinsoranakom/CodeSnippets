def test_mass_mail_sending(self):
        "Mass mail is redirected to a dummy outbox during test setup"
        response = self.client.get("/mass_mail_sending_view/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, "First Test message")
        self.assertEqual(mail.outbox[0].body, "This is the first test email")
        self.assertEqual(mail.outbox[0].from_email, "from@example.com")
        self.assertEqual(mail.outbox[0].to[0], "first@example.com")
        self.assertEqual(mail.outbox[0].to[1], "second@example.com")

        self.assertEqual(mail.outbox[1].subject, "Second Test message")
        self.assertEqual(mail.outbox[1].body, "This is the second test email")
        self.assertEqual(mail.outbox[1].from_email, "from@example.com")
        self.assertEqual(mail.outbox[1].to[0], "second@example.com")
        self.assertEqual(mail.outbox[1].to[1], "third@example.com")