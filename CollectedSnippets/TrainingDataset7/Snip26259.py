def test_send_messages_after_open_failed(self):
        """
        send_messages() shouldn't try to send messages if open() raises an
        exception after initializing the connection.
        """
        backend = smtp.EmailBackend()
        # Simulate connection initialization success and a subsequent
        # connection exception.
        backend.connection = mock.Mock(spec=object())
        backend.open = lambda: None
        email = EmailMessage(to=["to@example.com"])
        self.assertEqual(backend.send_messages([email]), 0)