def test_address_header_injection(self):
        msg = "Header values may not contain linefeed or carriage return characters"
        cases = [
            "Name\nInjection <to@example.com>",
            '"Name\nInjection" <to@example.com>',
            '"Name\rInjection" <to@example.com>',
            '"Name\r\nInjection" <to@example.com>',
            "Name <to\ninjection@example.com>",
            "to\ninjection@example.com",
        ]

        # Structured address header fields (from RFC 5322 3.6.x).
        headers = [
            "From",
            "Sender",
            "Reply-To",
            "To",
            "Cc",
            # "Bcc" is not checked by EmailMessage.message().
            # See SMTPBackendTests.test_avoids_sending_to_invalid_addresses().
            "Resent-From",
            "Resent-Sender",
            "Resent-To",
            "Resent-Cc",
            "Resent-Bcc",
        ]

        for header in headers:
            for email_address in cases:
                with self.subTest(header=header, email_address=email_address):
                    # Construct an EmailMessage with header set to
                    # email_address. Specific constructor params vary by
                    # header.
                    if header == "From":
                        email = EmailMessage(from_email=email_address)
                    elif header in ("To", "Cc", "Bcc", "Reply-To"):
                        param = header.lower().replace("-", "_")
                        email = EmailMessage(**{param: [email_address]})
                    else:
                        email = EmailMessage(headers={header: email_address})
                    with self.assertRaisesMessage(ValueError, msg):
                        email.message()