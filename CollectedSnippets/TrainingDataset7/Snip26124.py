def test_attach_text_as_bytes(self):
        """
        For text/* attachments, EmailMessage.attach() decodes bytes as UTF-8
        if possible and changes to DEFAULT_ATTACHMENT_MIME_TYPE if not.
        """
        email = EmailMessage()
        # Mimetype guessing identifies these as text/plain from the .txt
        # extensions.
        email.attach("utf8.txt", "ütƒ-8\n".encode())
        email.attach("not-utf8.txt", b"\x86unknown-encoding\n")
        attachments = self.get_decoded_attachments(email)
        self.assertEqual(attachments[0], ("utf8.txt", "ütƒ-8\n", "text/plain"))
        self.assertEqual(
            attachments[1],
            ("not-utf8.txt", b"\x86unknown-encoding\n", "application/octet-stream"),
        )