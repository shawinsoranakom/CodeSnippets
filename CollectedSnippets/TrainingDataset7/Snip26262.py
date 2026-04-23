def test_avoids_sending_to_invalid_addresses(self):
        """
        Verify invalid addresses can't sneak into SMTP commands through
        EmailMessage.all_recipients() (which is distinct from message header
        fields).
        """
        backend = smtp.EmailBackend()
        backend.connection = mock.Mock()
        for email_address in (
            # Invalid address with two @ signs.
            "to@other.com@example.com",
            # Invalid address without the quotes.
            "to@other.com <to@example.com>",
            # Multiple mailboxes in a single address.
            "to@example.com, other@example.com",
            # Other invalid addresses.
            "@",
            "to@",
            "@example.com",
            # CR/NL in addr-spec. (SMTP strips display-name.)
            '"evil@example.com\r\nto"@example.com',
            "to\nevil@example.com",
        ):
            with self.subTest(email_address=email_address):
                # Use bcc (which is only processed by SMTP backend) to ensure
                # error is coming from SMTP backend, not
                # EmailMessage.message().
                email = EmailMessage(bcc=[email_address])
                with self.assertRaisesMessage(ValueError, "Invalid address"):
                    backend.send_messages([email])