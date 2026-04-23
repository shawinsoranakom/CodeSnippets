def test_set_autocommit_health_checks_enabled(self):
        self.patch_settings_dict(conn_health_checks=True)
        self.assertIsNone(connection.connection)
        # Newly created connections are considered healthy without performing
        # the health check.
        with patch.object(connection, "is_usable", side_effect=AssertionError):
            # Simulate outermost atomic block: changing autocommit for
            # a connection.
            connection.set_autocommit(False)
            self.run_query()
            connection.commit()
            connection.set_autocommit(True)

        old_connection = connection.connection
        # Simulate request_finished.
        connection.close_if_unusable_or_obsolete()
        # Persistent connections are enabled.
        self.assertIs(old_connection, connection.connection)

        # Simulate connection health check failing.
        with patch.object(
            connection, "is_usable", return_value=False
        ) as mocked_is_usable:
            # Simulate outermost atomic block: changing autocommit for
            # a connection.
            connection.set_autocommit(False)
            new_connection = connection.connection
            self.assertIsNot(new_connection, old_connection)
            # Only one health check per "request" is performed, so a query will
            # carry on even if the health check fails. This query succeeds
            # because the real connection is healthy and only the health check
            # failure is mocked.
            self.run_query()
            connection.commit()
            connection.set_autocommit(True)
            # The connection is unchanged.
            self.assertIs(new_connection, connection.connection)
        self.assertEqual(mocked_is_usable.call_count, 1)

        # Simulate request_finished.
        connection.close_if_unusable_or_obsolete()
        # The underlying connection is being reused further with health checks
        # succeeding.
        connection.set_autocommit(False)
        self.run_query()
        connection.commit()
        connection.set_autocommit(True)
        self.assertIs(new_connection, connection.connection)