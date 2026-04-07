def test_from_header(self):
        """
        Make sure we can manually set the From header (#9214)
        """
        email = EmailMessage(
            from_email="bounce@example.com",
            headers={"From": "from@example.com"},
        )
        message = email.message()
        self.assertEqual(message.get_all("From"), ["from@example.com"])