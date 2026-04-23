def test_html_send_mail(self):
        """Test html_message argument to send_mail"""
        send_mail(
            "Subject",
            "Content\n",
            "sender@example.com",
            ["nobody@example.com"],
            html_message="HTML Content\n",
        )
        message = self.get_the_message()

        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get_all("to"), ["nobody@example.com"])
        self.assertTrue(message.is_multipart())
        self.assertEqual(len(message.get_payload()), 2)
        self.assertEqual(message.get_payload(0).get_content(), "Content\n")
        self.assertEqual(message.get_payload(0).get_content_type(), "text/plain")
        self.assertEqual(message.get_payload(1).get_content(), "HTML Content\n")
        self.assertEqual(message.get_payload(1).get_content_type(), "text/html")