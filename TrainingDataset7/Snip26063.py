def test_attachments_mimebase_in_constructor(self):
        txt = MIMEText("content1")
        msg = EmailMessage(attachments=[txt])
        payload = msg.message().get_payload()
        self.assertEqual(payload[0], txt)