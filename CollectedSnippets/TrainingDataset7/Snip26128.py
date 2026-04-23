def test_attach_8bit_rfc822_message_non_ascii(self):
        """
        Attaching a message that uses 8bit content transfer encoding for
        non-ASCII characters should not raise a UnicodeEncodeError (#36119).
        """
        attachment = dedent("""\
            Subject: A message using 8bit CTE
            Content-Type: text/plain; charset=utf-8
            Content-Transfer-Encoding: 8bit

            ¡8-bit content!
            """).encode()
        email = EmailMessage()
        email.attach("attachment.eml", attachment, "message/rfc822")
        attachments = self.get_raw_attachments(email)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].get_content_type(), "message/rfc822")
        attached_message = attachments[0].get_content()
        self.assertEqual(attached_message.get_content().rstrip(), "¡8-bit content!")
        self.assertEqual(attached_message["Content-Transfer-Encoding"], "8bit")
        self.assertEqual(attached_message.get_content_type(), "text/plain")