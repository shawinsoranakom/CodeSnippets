def test_encoding(self):
        """
        Regression for #12791 - Encode body correctly with other encodings
        than utf-8
        """
        email = EmailMessage(body="Firstname Sürname is a great guy.\n")
        email.encoding = "iso-8859-1"
        message = email.message()
        self.assertEqual(message["Content-Type"], 'text/plain; charset="iso-8859-1"')

        # Check that body is actually encoded with iso-8859-1.
        msg_bytes = message.as_bytes()
        self.assertEqual(message["Content-Transfer-Encoding"], "8bit")
        self.assertIn(b"Firstname S\xfc", msg_bytes)
        parsed = message_from_bytes(msg_bytes)
        self.assertEqual(parsed.get_content(), "Firstname Sürname is a great guy.\n")