def test_encoding_alternatives(self):
        """
        Encode alternatives correctly with other encodings than utf-8.
        """
        text_content = "Firstname Sürname is a great guy.\n"
        html_content = "<p>Firstname Sürname is a <strong>great</strong> guy.</p>\n"
        email = EmailMultiAlternatives(body=text_content)
        email.encoding = "iso-8859-1"
        email.attach_alternative(html_content, "text/html")
        message = email.message()
        # Check both parts are sent using the specified encoding.
        self.assertEqual(
            message.get_payload(0)["Content-Type"], 'text/plain; charset="iso-8859-1"'
        )
        self.assertEqual(
            message.get_payload(1)["Content-Type"], 'text/html; charset="iso-8859-1"'
        )

        # Check both parts decode to the original content at the receiving end.
        parsed = message_from_bytes(message.as_bytes())
        self.assertEqual(parsed.get_body(("plain",)).get_content(), text_content)
        self.assertEqual(parsed.get_body(("html",)).get_content(), html_content)