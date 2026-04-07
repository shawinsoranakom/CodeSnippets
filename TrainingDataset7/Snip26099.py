def test_reply_to_header(self):
        """
        Specifying 'Reply-To' in headers should override reply_to.
        """
        email = EmailMessage(
            reply_to=["foo@example.com"],
            headers={"Reply-To": "override@example.com"},
        )
        message = email.message()
        self.assertEqual(message.get_all("Reply-To"), ["override@example.com"])