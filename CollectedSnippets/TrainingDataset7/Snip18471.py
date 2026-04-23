def setUp(self):
        # All test cases here need newly configured and created connections.
        # Use the default db connection for convenience.
        connection.close()
        self.addCleanup(connection.close)