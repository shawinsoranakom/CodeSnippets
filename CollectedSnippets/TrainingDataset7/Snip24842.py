def setUp(self):
        # Disable the request_finished signal during this test
        # to avoid interfering with the database connection.
        request_finished.disconnect(close_old_connections)
        self.addCleanup(request_finished.connect, close_old_connections)