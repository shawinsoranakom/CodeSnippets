def test_attach_mime_image_in_constructor(self):
        msg = (
            "MIMEBase attachments are deprecated."
            " Use an email.message.MIMEPart instead."
        )
        image = MIMEImage(b"\x89PNG...", "png")
        image["Content-Disposition"] = "attachment; filename=test.png"
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
            email = EmailMessage(attachments=[image])

        attachments = self.get_raw_attachments(email)
        self.assertEqual(len(attachments), 1)
        image_att = attachments[0]
        self.assertEqual(image_att.get_content_type(), "image/png")
        self.assertEqual(image_att.get_content(), b"\x89PNG...")
        self.assertEqual(image_att.get_filename(), "test.png")