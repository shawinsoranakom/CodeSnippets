def test_reply_to_in_headers_only(self):
        message = EmailMessage(
            headers={"Reply-To": "reply_to@example.com"},
        ).message()
        self.assertEqual(message.get_all("Reply-To"), ["reply_to@example.com"])