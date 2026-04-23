def test_body_contains(self):
        email_msg = EmailMultiAlternatives()
        email_msg.body = "I am content."
        self.assertIs(email_msg.body_contains("I am"), True)
        self.assertIs(email_msg.body_contains("I am content."), True)

        email_msg.attach_alternative("<p>I am different content.</p>", "text/html")
        self.assertIs(email_msg.body_contains("I am"), True)
        self.assertIs(email_msg.body_contains("I am content."), False)
        self.assertIs(email_msg.body_contains("<p>I am different content.</p>"), False)