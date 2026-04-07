def test_connection_timeout_default(self):
        """The connection's timeout value is None by default."""
        connection = mail.get_connection("django.core.mail.backends.smtp.EmailBackend")
        self.assertIsNone(connection.timeout)