def test_attach_utf8_text_as_bytes(self):
        """
        Non-ASCII characters encoded as valid UTF-8 are correctly transported
        in a form that can be decoded at the receiving end.
        """
        msg = EmailMessage()
        msg.attach("file.txt", b"\xc3\xa4\n")  # UTF-8 encoded a-umlaut.
        filename, content, mimetype = self.get_decoded_attachments(msg)[0]
        self.assertEqual(filename, "file.txt")
        self.assertEqual(content, "ä\n")  # (decoded)
        self.assertEqual(mimetype, "text/plain")