def test_plaintext_send_mail(self):
        """
        Test send_mail without the html_message
        regression test for adding html_message parameter to send_mail()
        """
        send_mail("Subject", "Content\n", "sender@example.com", ["nobody@example.com"])
        message = self.get_the_message()

        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get_all("to"), ["nobody@example.com"])
        self.assertFalse(message.is_multipart())
        self.assertEqual(message.get_content(), "Content\n")
        self.assertEqual(message.get_content_type(), "text/plain")