def test_attach_mime_part(self):
        """
        EmailMessage.attach() docs: "You can pass it
        a single argument that is a MIMEPart object."
        """
        # This also verifies complex attachments with extra header fields.
        email = EmailMessage()
        image = MIMEPart()
        image.set_content(
            b"GIF89a...",
            maintype="image",
            subtype="gif",
            disposition="inline",
            cid="<content-id@example.org>",
        )
        email.attach(image)

        attachments = self.get_raw_attachments(email)
        self.assertEqual(len(attachments), 1)
        image_att = attachments[0]
        self.assertEqual(image_att.get_content_type(), "image/gif")
        self.assertEqual(image_att.get_content_disposition(), "inline")
        self.assertEqual(image_att["Content-ID"], "<content-id@example.org>")
        self.assertEqual(image_att.get_content(), b"GIF89a...")
        self.assertIsNone(image_att.get_filename())