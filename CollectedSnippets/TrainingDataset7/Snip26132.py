def test_attach_mime_part_in_constructor(self):
        image = MIMEPart()
        image.set_content(
            b"\x89PNG...", maintype="image", subtype="png", filename="test.png"
        )
        email = EmailMessage(attachments=[image])

        attachments = self.get_raw_attachments(email)
        self.assertEqual(len(attachments), 1)
        image_att = attachments[0]
        self.assertEqual(image_att.get_content_type(), "image/png")
        self.assertEqual(image_att.get_content(), b"\x89PNG...")
        self.assertEqual(image_att.get_content_disposition(), "attachment")
        self.assertEqual(image_att.get_filename(), "test.png")