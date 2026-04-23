def test_server_open(self):
        """
        open() returns whether it opened a connection.
        """
        backend = smtp.EmailBackend(username="", password="")
        self.assertIsNone(backend.connection)
        opened = backend.open()
        backend.close()
        self.assertIs(opened, True)