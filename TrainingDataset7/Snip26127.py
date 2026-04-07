def test_attach_non_utf8_text_as_bytes(self):
        """
        Binary data that can't be decoded as UTF-8 overrides the MIME type
        instead of decoding the data.
        """
        msg = EmailMessage()
        msg.attach("file.txt", b"\xff")  # Invalid UTF-8.
        filename, content, mimetype = self.get_decoded_attachments(msg)[0]
        self.assertEqual(filename, "file.txt")
        # Content should be passed through unmodified.
        self.assertEqual(content, b"\xff")
        self.assertEqual(mimetype, "application/octet-stream")