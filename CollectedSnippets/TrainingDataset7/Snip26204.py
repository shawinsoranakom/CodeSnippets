def test_recipient_without_domain(self):
        """
        Regression test for #15042
        """
        self.assertTrue(send_mail("Subject", "Content", "tester", ["django"]))
        message = self.get_the_message()
        self.assertEqual(message.get("from"), "tester")
        self.assertEqual(message.get("to"), "django")