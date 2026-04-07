def test_dont_mangle_from_in_body(self):
        # Regression for #13433 - Make sure that EmailMessage doesn't mangle
        # 'From ' in message body.
        email = EmailMessage(body="From the future")
        self.assertNotIn(b">From the future", email.message().as_bytes())