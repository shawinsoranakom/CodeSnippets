def test_health_checks_enabled(self):
        self.patch_settings_dict(conn_health_checks=True)
        self.assertIsNone(connection.connection)
        # Newly created connections are considered healthy without performing
        # the health check.
        with patch.object(connection, "is_usable", side_effect=AssertionError):
            self.run_query()

        old_connection = connection.connection
        # Simulate request_finished.
        connection.close_if_unusable_or_obsolete()
        self.assertIs(old_connection, connection.connection)

        # Simulate connection health check failing.
        with patch.object(
            connection, "is_usable", return_value=False
        ) as mocked_is_usable:
            self.run_query()
            new_connection = connection.connection
            # A new connection is established.
            self.assertIsNot(new_connection, old_connection)
            # Only one health check per "request" is performed, so the next
            # query will carry on even if the health check fails. Next query
            # succeeds because the real connection is healthy and only the
            # health check failure is mocked.
            self.run_query()
            self.assertIs(new_connection, connection.connection)
        self.assertEqual(mocked_is_usable.call_count, 1)

        # Simulate request_finished.
        connection.close_if_unusable_or_obsolete()
        # The underlying connection is being reused further with health checks
        # succeeding.
        self.run_query()
        self.run_query()
        self.assertIs(new_connection, connection.connection)