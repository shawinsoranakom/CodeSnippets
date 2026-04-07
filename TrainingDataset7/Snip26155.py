def test_body_contains_alternative_non_text(self):
        email_msg = EmailMultiAlternatives()
        email_msg.body = "I am content."
        email_msg.attach_alternative("I am content.", "text/html")
        email_msg.attach_alternative(b"I am a song.", "audio/mpeg")
        self.assertIs(email_msg.body_contains("I am content"), True)