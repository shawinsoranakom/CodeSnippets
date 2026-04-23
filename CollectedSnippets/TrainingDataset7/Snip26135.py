def test_attach_content_is_required(self):
        email_msg = EmailMessage()
        msg = "content must be provided."
        with self.assertRaisesMessage(ValueError, msg):
            email_msg.attach("file.txt", mimetype="application/pdf")