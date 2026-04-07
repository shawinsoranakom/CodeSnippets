def test_non_utf8_headers_multipart(self):
        """
        Make sure headers can be set with a different encoding than utf-8 in
        EmailMultiAlternatives as well.
        """
        headers = {"Date": "Fri, 09 Nov 2001 01:08:47 -0000", "Message-ID": "foo"}
        from_email = "from@example.com"
        to = '"Sürname, Firstname" <to@example.com>'
        text_content = "This is an important message."
        html_content = "<p>This is an <strong>important</strong> message.</p>"
        email = EmailMultiAlternatives(
            "Message from Firstname Sürname",
            text_content,
            from_email,
            [to],
            headers=headers,
        )
        email.attach_alternative(html_content, "text/html")
        email.encoding = "iso-8859-1"
        message = email.message()

        # Verify sent headers use RFC 2047 encoded-words, not raw utf-8.
        msg_bytes = message.as_bytes()
        self.assertTrue(msg_bytes.isascii())

        # Verify sent headers parse to original values.
        parsed = message_from_bytes(msg_bytes)
        self.assertEqual(parsed["Subject"], "Message from Firstname Sürname")
        self.assertEqual(
            parsed["To"].addresses,
            (Address(display_name="Sürname, Firstname", addr_spec="to@example.com"),),
        )