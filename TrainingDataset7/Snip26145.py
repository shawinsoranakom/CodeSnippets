def test_body_content_transfer_encoding(self):
        # Shouldn't use base64 or quoted-printable, instead should detect it
        # can represent content with 7-bit data (#3472, #11212).
        msg = EmailMessage(body="Body with only ASCII characters.")
        s = msg.message().as_bytes()
        self.assertIn(b"Content-Transfer-Encoding: 7bit", s)

        # Shouldn't use base64 or quoted-printable, instead should detect
        # it can represent content with 8-bit data.
        msg = EmailMessage(body="Body with latin characters: àáä.")
        s = msg.message().as_bytes()
        self.assertIn(b"Content-Transfer-Encoding: 8bit", s)

        # Long body lines that require folding should use quoted-printable or
        # base64, whichever is shorter.
        msg = EmailMessage(
            body=(
                "Body with non latin characters: А Б В Г Д Е Ж Ѕ З И І К Л М Н О П.\n"
                "Because it has a line > 78 utf-8 octets, it should be folded, and "
                "must then be encoded using the shorter of quoted-printable or base64."
            ),
        )
        s = msg.message().as_bytes()
        self.assertIn(b"Content-Transfer-Encoding: quoted-printable", s)