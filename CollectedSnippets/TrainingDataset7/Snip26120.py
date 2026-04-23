def test_attachments_with_alternative_parts(self):
        """
        Message with attachment and alternative has correct structure (#9367).
        """
        text_content = "This is an important message."
        html_content = "<p>This is an <strong>important</strong> message.</p>"
        msg = EmailMultiAlternatives(body=text_content)
        msg.attach_alternative(html_content, "text/html")
        msg.attach("an attachment.pdf", b"%PDF-1.4.%...", mimetype="application/pdf")
        msg_bytes = msg.message().as_bytes()
        message = message_from_bytes(msg_bytes)
        self.assertTrue(message.is_multipart())
        self.assertEqual(message.get_content_type(), "multipart/mixed")
        self.assertEqual(message.get_default_type(), "text/plain")
        payload = message.get_payload()
        self.assertEqual(payload[0].get_content_type(), "multipart/alternative")
        self.assertEqual(payload[1].get_content_type(), "application/pdf")