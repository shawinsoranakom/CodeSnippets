def test_attach_rfc822_message(self):
        """
        EmailMessage.attach() docs: "If you specify a mimetype of
        message/rfc822, it will also accept django.core.mail.EmailMessage and
        email.message.Message."
        """
        # django.core.mail.EmailMessage
        django_email = EmailMessage("child subject", "child body")
        # email.message.Message
        py_message = PyMessage()
        py_message["Subject"] = "child subject"
        py_message.set_payload("child body")
        # email.message.EmailMessage
        py_email_message = PyEmailMessage()
        py_email_message["Subject"] = "child subject"
        py_email_message.set_content("child body")

        cases = [
            django_email,
            py_message,
            py_email_message,
            # Should also allow message serialized as str or bytes.
            py_message.as_string(),
            py_message.as_bytes(),
        ]

        for child_message in cases:
            with self.subTest(child_type=child_message.__class__):
                email = EmailMessage("parent message", "parent body")
                email.attach(content=child_message, mimetype="message/rfc822")
                self.assertEqual(len(email.attachments), 1)
                self.assertIsInstance(email.attachments[0], EmailAttachment)
                self.assertEqual(email.attachments[0].mimetype, "message/rfc822")

                # Make sure it is serialized correctly: a message/rfc822
                # attachment whose "body" content (payload) is the
                # "encapsulated" (child) message.
                attachments = self.get_raw_attachments(email)
                self.assertEqual(len(attachments), 1)
                rfc822_attachment = attachments[0]
                self.assertEqual(rfc822_attachment.get_content_type(), "message/rfc822")

                attached_message = rfc822_attachment.get_content()
                self.assertEqual(attached_message["Subject"], "child subject")
                self.assertEqual(attached_message.get_content().rstrip(), "child body")

                # Regression for #18967: Per RFC 2046 5.2.1, "No encoding other
                # than '7bit', '8bit', or 'binary' is permitted for the body of
                # a 'message/rfc822' entity." (Default CTE is "7bit".)
                cte = rfc822_attachment.get("Content-Transfer-Encoding", "7bit")
                self.assertIn(cte, ("7bit", "8bit", "binary"))

                # Any properly declared CTE is allowed for the attached message
                # itself (including quoted-printable or base64). For the plain
                # ASCII content in this test, we'd expect 7bit.
                child_cte = attached_message.get("Content-Transfer-Encoding", "7bit")
                self.assertEqual(child_cte, "7bit")
                self.assertEqual(attached_message.get_content_type(), "text/plain")