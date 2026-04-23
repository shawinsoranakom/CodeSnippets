def test_in_memory_database_lock(self):
        """
        With a threaded LiveServer and an in-memory database, an error can
        occur when 2 requests reach the server and try to lock the database
        at the same time, if the requests do not share the same database
        connection.
        """
        conn = self.server_thread.connections_override[DEFAULT_DB_ALIAS]
        source_connection = conn.connection
        # Open a connection to the database.
        conn.connect()
        self.addCleanup(source_connection.close)
        # Create a transaction to lock the database.
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE TRANSACTION")
        self.addCleanup(cursor.execute, "ROLLBACK")
        try:
            with self.urlopen("/create_model_instance/") as f:
                self.assertEqual(f.status, 200)
        except HTTPError:
            self.fail("Unexpected error due to a database lock.")