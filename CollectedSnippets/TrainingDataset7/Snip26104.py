def test_unicode_headers(self):
        email = EmailMessage(
            subject="Gżegżółka",
            to=["to@example.com"],
            headers={
                "Sender": '"Firstname Sürname" <sender@example.com>',
                "Comments": "My Sürname is non-ASCII",
            },
        )
        message = email.message()

        # Verify sent headers use RFC 2047 encoded-words (not raw utf-8).
        # The exact encoding details don't matter so long as the result parses
        # to the original values.
        msg_bytes = message.as_bytes()
        self.assertTrue(msg_bytes.isascii())  # not unencoded utf-8.
        parsed = message_from_bytes(msg_bytes)
        self.assertEqual(parsed["Subject"], "Gżegżółka")
        self.assertEqual(
            parsed["Sender"].address,
            Address(display_name="Firstname Sürname", addr_spec="sender@example.com"),
        )
        self.assertEqual(parsed["Comments"], "My Sürname is non-ASCII")