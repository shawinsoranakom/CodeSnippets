def test_message_policy_smtputf8(self):
        # With SMTPUTF8, the message uses utf-8 directly in headers (not
        # RFC 2047 encoded-words). Note this is the only spec-compliant way
        # to send to a non-ASCII localpart.
        email = EmailMessage(
            subject="Detta ämne innehåller icke-ASCII-tecken",
            to=["nøn-åscîi@example.com"],
        )
        message = email.message(policy=policy.SMTPUTF8)
        self.assertEqual(message.policy, policy.SMTPUTF8)
        msg_bytes = message.as_bytes()
        self.assertIn(
            "Subject: Detta ämne innehåller icke-ASCII-tecken".encode(), msg_bytes
        )
        self.assertIn("To: nøn-åscîi@example.com".encode(), msg_bytes)
        self.assertNotIn(b"=?utf-8?", msg_bytes)