def test_health_checks_enabled_errors_occurred(self):
        self.patch_settings_dict(conn_health_checks=True)
        self.assertIsNone(connection.connection)
        # Newly created connections are considered healthy without performing
        # the health check.
        with patch.object(connection, "is_usable", side_effect=AssertionError):
            self.run_query()

        old_connection = connection.connection
        # Simulate errors_occurred.
        connection.errors_occurred = True
        # Simulate request_started (the connection is healthy).
        connection.close_if_unusable_or_obsolete()
        # Persistent connections are enabled.
        self.assertIs(old_connection, connection.connection)
        # No additional health checks after the one in
        # close_if_unusable_or_obsolete() are executed during this "request"
        # when running queries.
        with patch.object(connection, "is_usable", side_effect=AssertionError):
            self.run_query()