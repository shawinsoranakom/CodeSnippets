def test_mail_sending(self):
        "Mail is redirected to a dummy outbox during test setup"
        response = self.client.get("/mail_sending_view/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Test message")
        self.assertEqual(mail.outbox[0].body, "This is a test email")
        self.assertEqual(mail.outbox[0].from_email, "from@example.com")
        self.assertEqual(mail.outbox[0].to[0], "first@example.com")
        self.assertEqual(mail.outbox[0].to[1], "second@example.com")