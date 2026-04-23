def test_connection_arg_mail_admins(self):
        mail.outbox = []
        # Send using non-default connection.
        connection = mail.get_connection("mail.custombackend.EmailBackend")
        mail_admins("Admin message", "Content", connection=connection)
        self.assertEqual(mail.outbox, [])
        self.assertEqual(len(connection.test_outbox), 1)
        self.assertEqual(connection.test_outbox[0].subject, "[Django] Admin message")