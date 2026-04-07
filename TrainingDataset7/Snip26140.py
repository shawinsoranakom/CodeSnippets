def test_connection_arg_send_mail(self):
        mail.outbox = []
        # Send using non-default connection.
        connection = mail.get_connection("mail.custombackend.EmailBackend")
        send_mail(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            connection=connection,
        )
        self.assertEqual(mail.outbox, [])
        self.assertEqual(len(connection.test_outbox), 1)
        self.assertEqual(connection.test_outbox[0].subject, "Subject")