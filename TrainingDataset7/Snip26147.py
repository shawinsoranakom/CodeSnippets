def test_sanitize_address_invalid(self):
        # Tests the internal sanitize_address() function. Note that Django's
        # EmailMessage.message() will not catch these cases, as it only calls
        # sanitize_address() if an address also includes non-ASCII chars.
        # Django detects these cases in the SMTP EmailBackend during sending.
        # See SMTPBackendTests.test_avoids_sending_to_invalid_addresses()
        # below.
        from django.core.mail.message import sanitize_address

        for email_address in (
            # Invalid address with two @ signs.
            "to@other.com@example.com",
            # Invalid address without the quotes.
            "to@other.com <to@example.com>",
            # Other invalid addresses.
            "@",
            "to@",
            "@example.com",
            ("", ""),
        ):
            with self.subTest(email_address=email_address):
                with self.assertRaisesMessage(ValueError, "Invalid address"):
                    sanitize_address(email_address, encoding="utf-8")