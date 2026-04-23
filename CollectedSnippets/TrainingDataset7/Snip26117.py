def test_attachments_constructor(self):
        file_name = "example.txt"
        file_content = "Text file content\n"
        mime_type = "text/plain"
        msg = EmailMessage(
            attachments=[EmailAttachment(file_name, file_content, mime_type)]
        )

        self.assertIsInstance(msg.attachments[0], EmailAttachment)

        self.assertEqual(msg.attachments[0][0], file_name)
        self.assertEqual(msg.attachments[0].filename, file_name)

        self.assertEqual(msg.attachments[0][1], file_content)
        self.assertEqual(msg.attachments[0].content, file_content)

        self.assertEqual(msg.attachments[0][2], mime_type)
        self.assertEqual(msg.attachments[0].mimetype, mime_type)

        attachments = self.get_decoded_attachments(msg)
        self.assertEqual(attachments[0], (file_name, file_content, mime_type))