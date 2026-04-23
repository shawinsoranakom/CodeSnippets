def test_localpart_only_address(self):
        """
        Django allows sending to a localpart-only email address
        (without @domain). This is not a valid RFC 822/2822/5322 addr-spec, but
        is accepted by some SMTP servers for local delivery.
        Regression for #15042.
        """
        email = EmailMessage(to=["localpartonly"])
        parsed = message_from_bytes(email.message().as_bytes())
        self.assertEqual(
            parsed["To"].addresses, (Address(username="localpartonly", domain=""),)
        )