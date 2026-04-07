def test_send_long_lines(self):
        """
        Email line length is limited to 998 chars by the RFC 5322 Section
        2.1.1. A message body containing longer lines is converted to
        quoted-printable or base64 (whichever is shorter), to avoid having to
        insert newlines in a way that alters the intended text.
        """
        cases = [
            # (body, expected_cte)
            ("В южных морях " * 60, "base64"),
            ("I de sørlige hav " * 58, "quoted-printable"),
        ]
        for body, expected_cte in cases:
            with self.subTest(body=f"{body[:10]}…", expected_cte=expected_cte):
                self.flush_mailbox()
                # Test precondition: Body is a single line < 998 characters,
                # but utf-8 encoding of body is > 998 octets (forcing a CTE
                # that avoids inserting newlines).
                self.assertLess(len(body), 998)
                self.assertGreater(len(body.encode()), 998)

                email = EmailMessage(body=body, to=["to@example.com"])
                email.send()
                message = self.get_the_message()
                self.assertMessageHasHeaders(
                    message,
                    {
                        ("MIME-Version", "1.0"),
                        ("Content-Type", 'text/plain; charset="utf-8"'),
                        ("Content-Transfer-Encoding", expected_cte),
                    },
                )