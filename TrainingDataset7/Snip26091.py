def test_recipients_as_string(self):
        with self.assertRaisesMessage(
            TypeError, '"to" argument must be a list or tuple'
        ):
            EmailMessage(to="foo@example.com")
        with self.assertRaisesMessage(
            TypeError, '"cc" argument must be a list or tuple'
        ):
            EmailMessage(cc="foo@example.com")
        with self.assertRaisesMessage(
            TypeError, '"bcc" argument must be a list or tuple'
        ):
            EmailMessage(bcc="foo@example.com")
        with self.assertRaisesMessage(
            TypeError, '"reply_to" argument must be a list or tuple'
        ):
            EmailMessage(reply_to="reply_to@example.com")