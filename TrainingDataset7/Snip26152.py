def test_email_multi_alternatives_content_mimetype_none(self):
        email_msg = EmailMultiAlternatives()
        msg = "Both content and mimetype must be provided."
        with self.assertRaisesMessage(ValueError, msg):
            email_msg.attach_alternative(None, "text/html")
        with self.assertRaisesMessage(ValueError, msg):
            email_msg.attach_alternative("<p>content</p>", None)