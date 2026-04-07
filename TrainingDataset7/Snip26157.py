def test_positional_arguments_order(self):
        """
        EmailMessage class docs: "… is initialized with the following
        parameters (in the given order, if positional arguments are used)."
        """
        connection = mail.get_connection()
        email = EmailMessage(
            # (If you need to insert/remove/reorder any params here,
            # that indicates a breaking change to documented behavior.)
            "subject",
            "body\n",
            "from@example.com",
            ["to@example.com"],
            # (New options can be added below here as keyword-only args.)
            bcc=["bcc@example.com"],
            connection=connection,
            attachments=[EmailAttachment("file.txt", "attachment\n", "text/plain")],
            headers={"X-Header": "custom header"},
            cc=["cc@example.com"],
            reply_to=["reply-to@example.com"],
        )

        message = email.message()
        self.assertEqual(message.get_all("Subject"), ["subject"])
        self.assertEqual(message.get_all("From"), ["from@example.com"])
        self.assertEqual(message.get_all("To"), ["to@example.com"])
        self.assertEqual(message.get_all("X-Header"), ["custom header"])
        self.assertEqual(message.get_all("Cc"), ["cc@example.com"])
        self.assertEqual(message.get_all("Reply-To"), ["reply-to@example.com"])
        self.assertEqual(message.get_payload(0).get_payload(), "body\n")
        self.assertEqual(
            self.get_decoded_attachments(email),
            [("file.txt", "attachment\n", "text/plain")],
        )
        self.assertEqual(
            email.recipients(), ["to@example.com", "cc@example.com", "bcc@example.com"]
        )
        self.assertIs(email.get_connection(), connection)