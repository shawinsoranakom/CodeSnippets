def test_closes_connections(self):
        # The server's request thread sets this event after closing
        # its database connections.
        closed_event = self.server_thread.httpd._connections_closed
        conn = self.conn
        # Open a connection to the database.
        conn.connect()
        self.assertIsNotNone(conn.connection)
        with self.urlopen("/model_view/") as f:
            # The server can access the database.
            self.assertCountEqual(f.read().splitlines(), [b"jane", b"robert"])
        # Wait for the server's request thread to close the connection.
        # A timeout of 0.1 seconds should be more than enough. If the wait
        # times out, the assertion after should fail.
        closed_event.wait(timeout=0.1)
        self.assertIsNone(conn.connection)