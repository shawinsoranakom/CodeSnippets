def test_idn_send(self):
        """
        Regression test for #14301
        """
        self.assertTrue(send_mail("Subject", "Content", "from@öäü.com", ["to@öäü.com"]))
        message = self.get_the_message()
        self.assertEqual(message.get("from"), "from@xn--4ca9at.com")
        self.assertEqual(message.get("to"), "to@xn--4ca9at.com")

        self.flush_mailbox()
        m = EmailMessage(
            from_email="from@öäü.com", to=["to@öäü.com"], cc=["cc@öäü.com"]
        )
        m.send()
        message = self.get_the_message()
        self.assertEqual(message.get("from"), "from@xn--4ca9at.com")
        self.assertEqual(message.get("to"), "to@xn--4ca9at.com")
        self.assertEqual(message.get("cc"), "cc@xn--4ca9at.com")