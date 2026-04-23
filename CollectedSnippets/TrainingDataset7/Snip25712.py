def test_suspicious_email_admins(self):
        self.client.get("/suspicious/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("SuspiciousOperation at /suspicious/", mail.outbox[0].body)