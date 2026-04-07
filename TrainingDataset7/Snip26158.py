def test_all_params_can_be_set_before_send(self):
        """
        EmailMessage class docs: "All parameters … can be set at any time
        prior to calling the send() method."
        """
        # This is meant to verify EmailMessage.__init__() doesn't apply any
        # special processing that would be missing for properties set later.
        original_connection = mail.get_connection(username="original")
        new_connection = mail.get_connection(username="new")
        email = EmailMessage(
            "original subject",
            "original body\n",
            "original-from@example.com",
            ["original-to@example.com"],
            bcc=["original-bcc@example.com"],
            connection=original_connection,
            attachments=[
                EmailAttachment("original.txt", "original attachment\n", "text/plain")
            ],
            headers={"X-Header": "original header"},
            cc=["original-cc@example.com"],
            reply_to=["original-reply-to@example.com"],
        )
        email.subject = "new subject"
        email.body = "new body\n"
        email.from_email = "new-from@example.com"
        email.to = ["new-to@example.com"]
        email.bcc = ["new-bcc@example.com"]
        email.connection = new_connection
        image = MIMEPart()
        image.set_content(b"GIF89a...", "image", "gif")
        email.attachments = [
            ("new1.txt", "new attachment 1\n", "text/plain"),  # plain tuple
            EmailAttachment("new2.txt", "new attachment 2\n", "text/csv"),
            image,
        ]
        email.extra_headers = {"X-Header": "new header"}
        email.cc = ["new-cc@example.com"]
        email.reply_to = ["new-reply-to@example.com"]

        message = email.message()
        self.assertEqual(message.get_all("Subject"), ["new subject"])
        self.assertEqual(message.get_all("From"), ["new-from@example.com"])
        self.assertEqual(message.get_all("To"), ["new-to@example.com"])
        self.assertEqual(message.get_all("X-Header"), ["new header"])
        self.assertEqual(message.get_all("Cc"), ["new-cc@example.com"])
        self.assertEqual(message.get_all("Reply-To"), ["new-reply-to@example.com"])
        self.assertEqual(message.get_payload(0).get_payload(), "new body\n")
        self.assertEqual(
            self.get_decoded_attachments(email),
            [
                ("new1.txt", "new attachment 1\n", "text/plain"),
                ("new2.txt", "new attachment 2\n", "text/csv"),
                (None, b"GIF89a...", "image/gif"),
            ],
        )
        self.assertEqual(
            email.recipients(),
            ["new-to@example.com", "new-cc@example.com", "new-bcc@example.com"],
        )
        self.assertIs(email.get_connection(), new_connection)
        self.assertNotIn("original", message.as_string())