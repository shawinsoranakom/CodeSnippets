def test_email_msg_uses_crlf(self):
        """#23063 -- RFC-compliant messages are sent over SMTP."""
        send = SMTP.send
        try:
            smtp_messages = []

            def mock_send(self, s):
                smtp_messages.append(s)
                return send(self, s)

            SMTP.send = mock_send

            email = EmailMessage(
                "Subject", "Content", "from@example.com", ["to@example.com"]
            )
            mail.get_connection().send_messages([email])

            # Find the actual message
            msg = None
            for i, m in enumerate(smtp_messages):
                if m[:4] == "data":
                    msg = smtp_messages[i + 1]
                    break

            self.assertTrue(msg)

            msg = msg.decode()
            # The message only contains CRLF and not combinations of CRLF, LF,
            # and CR.
            msg = msg.replace("\r\n", "")
            self.assertNotIn("\r", msg)
            self.assertNotIn("\n", msg)

        finally:
            SMTP.send = send