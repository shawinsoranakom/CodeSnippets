def test_unicode_address_header(self):
        """
        Regression for #11144 - When a to/from/cc header contains Unicode,
        make sure the email addresses are parsed correctly (especially with
        regards to commas)
        """
        email = EmailMessage(
            to=['"Firstname Sürname" <to@example.com>', "other@example.com"],
        )
        parsed = message_from_bytes(email.message().as_bytes())
        self.assertEqual(
            parsed["To"].addresses,
            (
                Address(display_name="Firstname Sürname", addr_spec="to@example.com"),
                Address(addr_spec="other@example.com"),
            ),
        )

        email = EmailMessage(
            to=['"Sürname, Firstname" <to@example.com>', "other@example.com"],
        )
        parsed = message_from_bytes(email.message().as_bytes())
        self.assertEqual(
            parsed["To"].addresses,
            (
                Address(display_name="Sürname, Firstname", addr_spec="to@example.com"),
                Address(addr_spec="other@example.com"),
            ),
        )