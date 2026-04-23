def test_multiple_message_call(self):
        """
        Regression for #13259 - Make sure that headers are not changed when
        calling EmailMessage.message()
        """
        email = EmailMessage(
            from_email="bounce@example.com",
            headers={"From": "from@example.com"},
        )
        message = email.message()
        self.assertEqual(message.get_all("From"), ["from@example.com"])
        message = email.message()
        self.assertEqual(message.get_all("From"), ["from@example.com"])