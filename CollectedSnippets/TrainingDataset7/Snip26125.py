def test_attach_text_as_bytes_using_property(self):
        """
        The logic described in test_attach_text_as_bytes() also applies
        when directly setting the EmailMessage.attachments property.
        """
        email = EmailMessage()
        email.attachments = [
            ("utf8.txt", "ütƒ-8\n".encode(), "text/plain"),
            ("not-utf8.txt", b"\x86unknown-encoding\n", "text/plain"),
        ]
        attachments = self.get_decoded_attachments(email)
        self.assertEqual(len(attachments), 2)
        attachments = self.get_decoded_attachments(email)
        self.assertEqual(attachments[0], ("utf8.txt", "ütƒ-8\n", "text/plain"))
        self.assertEqual(
            attachments[1],
            ("not-utf8.txt", b"\x86unknown-encoding\n", "application/octet-stream"),
        )