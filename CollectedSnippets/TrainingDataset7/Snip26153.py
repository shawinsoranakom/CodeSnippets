def test_mime_structure(self):
        """
        Check generated messages have the expected MIME parts and nesting.
        """
        html_body = EmailAlternative("<p>HTML</p>", "text/html")
        image = EmailAttachment("image.gif", b"\x89PNG...", "image/png")
        rfc822_attachment = EmailAttachment(
            None, EmailMessage(body="text"), "message/rfc822"
        )
        cases = [
            # name, email (EmailMessage or subclass), expected structure
            (
                "single body",
                EmailMessage(body="text"),
                """
                text/plain
                """,
            ),
            (
                "single body with attachment",
                EmailMessage(body="text", attachments=[image]),
                """
                multipart/mixed
                    text/plain
                    image/png
                """,
            ),
            (
                "alternative bodies",
                EmailMultiAlternatives(body="text", alternatives=[html_body]),
                """
                multipart/alternative
                    text/plain
                    text/html
                """,
            ),
            (
                "alternative bodies with attachments",
                EmailMultiAlternatives(
                    body="text", alternatives=[html_body], attachments=[image]
                ),
                """
                multipart/mixed
                    multipart/alternative
                        text/plain
                        text/html
                    image/png
                """,
            ),
            (
                "alternative bodies with rfc822 attachment",
                EmailMultiAlternatives(
                    body="text",
                    alternatives=[html_body],
                    attachments=[rfc822_attachment],
                ),
                """
                multipart/mixed
                    multipart/alternative
                        text/plain
                        text/html
                    message/rfc822
                        text/plain
                """,
            ),
            (
                "attachment only",
                EmailMessage(attachments=[image]),
                # Avoid empty text/plain body.
                """
                multipart/mixed
                    image/png
                """,
            ),
            (
                "alternative only",
                EmailMultiAlternatives(alternatives=[html_body]),
                # Avoid empty text/plain body.
                """
                multipart/alternative
                    text/html
                """,
            ),
            (
                "alternative and attachment only",
                EmailMultiAlternatives(alternatives=[html_body], attachments=[image]),
                """
                multipart/mixed
                    multipart/alternative
                        text/html
                    image/png
                """,
            ),
            (
                "empty EmailMessage",
                EmailMessage(),
                """
                text/plain
                """,
            ),
            (
                "empty EmailMultiAlternatives",
                EmailMultiAlternatives(),
                """
                text/plain
                """,
            ),
        ]
        for name, email, expected in cases:
            expected = dedent(expected).lstrip()
            with self.subTest(name=name):
                message = email.message()
                structure = self.get_message_structure(message)
                self.assertEqual(structure, expected)