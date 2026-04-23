def test_encodes_idna_in_smtp_commands(self):
        """
        SMTP backend must encode non-ASCII domains for the SMTP envelope
        (which can be distinct from the email headers).
        """
        email = EmailMessage(
            from_email="lists@discussão.example.org",
            to=["To Example <to@漢字.example.com>"],
            bcc=["monitor@discussão.example.org"],
            headers={
                "From": "Gestor de listas <lists@discussão.example.org>",
                "To": "Discussão Django <django@discussão.example.org>",
            },
        )
        backend = smtp.EmailBackend()
        backend.send_messages([email])
        envelope = self.get_smtp_envelopes()[0]
        self.assertEqual(envelope["mail_from"], "lists@xn--discusso-xza.example.org")
        self.assertEqual(
            envelope["rcpt_tos"],
            ["to@xn--p8s937b.example.com", "monitor@xn--discusso-xza.example.org"],
        )