def test_decoded_attachment_text_MIMEPart(self):
        # See also test_attach_mime_part() and
        # test_attach_mime_part_in_constructor().
        txt = MIMEPart()
        txt.set_content("content1")
        msg = EmailMessage(attachments=[txt])
        payload = msg.message().get_payload()
        self.assertEqual(payload[0], txt)