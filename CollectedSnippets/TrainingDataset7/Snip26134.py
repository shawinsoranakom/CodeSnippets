def test_attach_mimepart_prohibits_other_params(self):
        email_msg = EmailMessage()
        txt = MIMEPart()
        txt.set_content("content")
        msg = (
            "content and mimetype must not be given when a MIMEPart instance "
            "is provided."
        )
        with self.assertRaisesMessage(ValueError, msg):
            email_msg.attach(txt, content="content")
        with self.assertRaisesMessage(ValueError, msg):
            email_msg.attach(txt, mimetype="text/plain")