def test_attach_file(self):
        """
        Test attaching a file against different mimetypes and make sure that
        a file will be attached and sent in some form even if a mismatched
        mimetype is specified.
        """
        files = (
            # filename, actual mimetype
            ("file.txt", "text/plain"),
            ("file.png", "image/png"),
            ("file_txt", None),
            ("file_png", None),
            ("file_txt.png", "image/png"),
            ("file_png.txt", "text/plain"),
            ("file.eml", "message/rfc822"),
        )
        test_mimetypes = ["text/plain", "image/png", None]

        for basename, real_mimetype in files:
            for mimetype in test_mimetypes:
                with self.subTest(
                    basename=basename, real_mimetype=real_mimetype, mimetype=mimetype
                ):
                    self.assertEqual(mimetypes.guess_type(basename)[0], real_mimetype)
                    expected_mimetype = (
                        mimetype or real_mimetype or "application/octet-stream"
                    )
                    file_path = Path(__file__).parent / "attachments" / basename
                    expected_content = file_path.read_bytes()
                    if expected_mimetype.startswith("text/"):
                        try:
                            expected_content = expected_content.decode()
                        except UnicodeDecodeError:
                            expected_mimetype = "application/octet-stream"

                    email = EmailMessage()
                    email.attach_file(file_path, mimetype=mimetype)

                    # Check EmailMessage.attachments.
                    self.assertEqual(len(email.attachments), 1)
                    self.assertEqual(email.attachments[0].filename, basename)
                    self.assertEqual(email.attachments[0].mimetype, expected_mimetype)
                    self.assertEqual(email.attachments[0].content, expected_content)

                    # Check attachments in the generated message.
                    # (The actual content is not checked as variations in
                    # platform line endings and rfc822 refolding complicate the
                    # logic.)
                    attachments = self.get_decoded_attachments(email)
                    self.assertEqual(len(attachments), 1)
                    actual = attachments[0]
                    self.assertEqual(actual.filename, basename)
                    self.assertEqual(actual.mimetype, expected_mimetype)