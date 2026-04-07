def test_message_header_overrides(self):
        """
        Specifying dates or message-ids in the extra headers overrides the
        default values (#9233)
        """
        headers = {"date": "Fri, 09 Nov 2001 01:08:47 -0000", "Message-ID": "foo"}
        email = EmailMessage(headers=headers)

        self.assertMessageHasHeaders(
            email.message(),
            {
                ("Message-ID", "foo"),
                ("date", "Fri, 09 Nov 2001 01:08:47 -0000"),
            },
        )