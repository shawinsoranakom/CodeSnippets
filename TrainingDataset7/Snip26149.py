def test_address_header_handling(self):
        # This verifies the modern email API's address header handling.
        cases = [
            # (address, expected_display_name, expected_addr_spec)
            ("to@example.com", "", "to@example.com"),
            # Addresses with display-names.
            ("A name <to@example.com>", "A name", "to@example.com"),
            ('"A name" <to@example.com>', "A name", "to@example.com"),
            (
                '"Comma, requires quotes" <to@example.com>',
                "Comma, requires quotes",
                "to@example.com",
            ),
            ('"to@other.com" <to@example.com>', "to@other.com", "to@example.com"),
            # Non-ASCII addr-spec: IDNA encoding for domain.
            # (Note: no RFC permits encoding a non-ASCII localpart.)
            ("to@éxample.com", "", "to@xn--xample-9ua.com"),
            (
                "To Example <to@éxample.com>",
                "To Example",
                "to@xn--xample-9ua.com",
            ),
            # Pre-encoded IDNA domain is left as is.
            # (Make sure IDNA 2008 is not downgraded to IDNA 2003.)
            ("to@xn--fa-hia.example.com", "", "to@xn--fa-hia.example.com"),
            (
                "<to@xn--10cl1a0b660p.example.com>",
                "",
                "to@xn--10cl1a0b660p.example.com",
            ),
            (
                '"Display, Name" <to@xn--nxasmm1c.example.com>',
                "Display, Name",
                "to@xn--nxasmm1c.example.com",
            ),
            # Non-ASCII display-name.
            ("Tó Example <to@example.com>", "Tó Example", "to@example.com"),
            # Addresses with two @ signs (quoted-string localpart).
            ('"to@other.com"@example.com', "", '"to@other.com"@example.com'),
            (
                'To Example <"to@other.com"@example.com>',
                "To Example",
                '"to@other.com"@example.com',
            ),
            # Addresses with long non-ASCII display names.
            (
                "Tó Example very long" * 4 + " <to@example.com>",
                "Tó Example very long" * 4,
                "to@example.com",
            ),
            # Address with long display name and non-ASCII domain.
            (
                "To Example very long" * 4 + " <to@exampl€.com>",
                "To Example very long" * 4,
                "to@xn--exampl-nc1c.com",
            ),
        ]
        for address, name, addr in cases:
            with self.subTest(address=address):
                email = EmailMessage(to=[address])
                parsed = message_from_bytes(email.message().as_bytes())
                actual = parsed["To"].addresses
                expected = (Address(display_name=name, addr_spec=addr),)
                self.assertEqual(actual, expected)