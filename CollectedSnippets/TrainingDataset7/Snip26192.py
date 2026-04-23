def test_send_verbose_name(self):
        email = EmailMessage(
            from_email='"Firstname Sürname" <from@example.com>',
            to=["to@example.com"],
        )
        email.send()
        message = self.get_the_message()
        self.assertEqual(message["from"], "Firstname Sürname <from@example.com>")