def test_subject_accepts_newlines(self):
        """
        Newlines in email reports' subjects are escaped to prevent
        AdminErrorHandler from failing (#17281).
        """
        message = "Message \r\n with newlines"
        expected_subject = "ERROR: Message \\r\\n with newlines"

        self.assertEqual(len(mail.outbox), 0)

        self.logger.error(message)

        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("\n", mail.outbox[0].subject)
        self.assertNotIn("\r", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].subject, expected_subject)