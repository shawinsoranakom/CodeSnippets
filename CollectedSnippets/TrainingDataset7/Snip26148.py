def test_sanitize_address_header_injection(self):
        # Tests the internal sanitize_address() function. These cases are
        # duplicated in test_address_header_handling(), which verifies headers
        # in the generated message.
        from django.core.mail.message import sanitize_address

        msg = "Invalid address; address parts cannot contain newlines."
        tests = [
            "Name\nInjection <to@example.com>",
            ("Name\nInjection", "to@xample.com"),
            "Name <to\ninjection@example.com>",
            ("Name", "to\ninjection@example.com"),
        ]
        for email_address in tests:
            with self.subTest(email_address=email_address):
                with self.assertRaisesMessage(ValueError, msg):
                    sanitize_address(email_address, encoding="utf-8")