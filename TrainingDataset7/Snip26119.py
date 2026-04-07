def test_attachments_constructor_omit_mimetype(self):
        """
        The mimetype can be omitted from an attachment tuple.
        """
        msg = EmailMessage(attachments=[("filename1", "content1")])
        filename, content, mimetype = self.get_decoded_attachments(msg)[0]
        self.assertEqual(filename, "filename1")
        self.assertEqual(content, b"content1")
        self.assertEqual(mimetype, "application/octet-stream")