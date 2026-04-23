def test_html_mail_admins(self):
        """Test html_message argument to mail_admins"""
        mail_admins("Subject", "Content\n", html_message="HTML Content\n")
        message = self.get_the_message()

        self.assertEqual(message.get("subject"), "[Django] Subject")
        self.assertEqual(message.get_all("to"), ["nobody@example.com"])
        self.assertTrue(message.is_multipart())
        self.assertEqual(len(message.get_payload()), 2)
        self.assertEqual(message.get_payload(0).get_content(), "Content\n")
        self.assertEqual(message.get_payload(0).get_content_type(), "text/plain")
        self.assertEqual(message.get_payload(1).get_content(), "HTML Content\n")
        self.assertEqual(message.get_payload(1).get_content_type(), "text/html")