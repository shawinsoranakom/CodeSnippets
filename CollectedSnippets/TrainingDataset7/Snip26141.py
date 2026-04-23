def test_connection_arg_send_mass_mail(self):
        mail.outbox = []
        # Send using non-default connection.
        connection = mail.get_connection("mail.custombackend.EmailBackend")
        send_mass_mail(
            [
                ("Subject1", "Content1", "from1@example.com", ["to1@example.com"]),
                ("Subject2", "Content2", "from2@example.com", ["to2@example.com"]),
            ],
            connection=connection,
        )
        self.assertEqual(mail.outbox, [])
        self.assertEqual(len(connection.test_outbox), 2)
        self.assertEqual(connection.test_outbox[0].subject, "Subject1")
        self.assertEqual(connection.test_outbox[1].subject, "Subject2")