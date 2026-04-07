def test_server_stopped(self):
        """
        Closing the backend while the SMTP server is stopped doesn't raise an
        exception.
        """
        self.backend.close()