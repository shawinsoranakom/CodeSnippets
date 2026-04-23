def test_alternative_alternatives(self):
        """
        Alternatives can be attached as either string or bytes
        and need not use a text/* mimetype.
        """
        cases = [
            # (mimetype, content, expected decoded payload)
            ("application/x-ccmail-rtf", b"non-text\x07bytes", b"non-text\x07bytes"),
            ("application/x-ccmail-rtf", "non-text\x07string", b"non-text\x07string"),
            ("text/x-amp-html", b"text bytes\n", b"text bytes\n"),
            ("text/x-amp-html", "text string\n", b"text string\n"),
        ]
        for mimetype, content, expected in cases:
            with self.subTest(case=(mimetype, content)):
                email = EmailMultiAlternatives()
                email.attach_alternative(content, mimetype)
                msg = email.message()
                self.assertEqual(msg.get_content_type(), "multipart/alternative")
                alternative = msg.get_payload()[0]
                self.assertEqual(alternative.get_content_type(), mimetype)
                self.assertEqual(alternative.get_payload(decode=True), expected)