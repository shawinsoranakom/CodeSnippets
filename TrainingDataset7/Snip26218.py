def test_file_sessions(self):
        """Make sure opening a connection creates a new file"""
        msg = EmailMessage(
            "Subject",
            "Content",
            "bounce@example.com",
            ["to@example.com"],
            headers={"From": "from@example.com"},
        )
        connection = mail.get_connection()
        connection.send_messages([msg])

        self.assertEqual(len(os.listdir(self.tmp_dir)), 1)
        with open(os.path.join(self.tmp_dir, os.listdir(self.tmp_dir)[0]), "rb") as fp:
            message = message_from_binary_file(fp, policy=policy.default)
        self.assertEqual(message.get_content_type(), "text/plain")
        self.assertEqual(message.get("subject"), "Subject")
        self.assertEqual(message.get("from"), "from@example.com")
        self.assertEqual(message.get("to"), "to@example.com")

        connection2 = mail.get_connection()
        connection2.send_messages([msg])
        self.assertEqual(len(os.listdir(self.tmp_dir)), 2)

        connection.send_messages([msg])
        self.assertEqual(len(os.listdir(self.tmp_dir)), 2)

        msg.connection = mail.get_connection()
        self.assertTrue(connection.open())
        msg.send()
        self.assertEqual(len(os.listdir(self.tmp_dir)), 3)
        msg.send()
        self.assertEqual(len(os.listdir(self.tmp_dir)), 3)

        connection.close()