def test_connect_isolation_level(self):
        """
        The transaction level can be configured with
        DATABASES ['OPTIONS']['isolation_level'].
        """
        from django.db.backends.postgresql.psycopg_any import IsolationLevel

        # Since this is a django.test.TestCase, a transaction is in progress
        # and the isolation level isn't reported as 0. This test assumes that
        # PostgreSQL is configured with the default isolation level.
        # Check the level on the psycopg connection, not the Django wrapper.
        self.assertIsNone(connection.connection.isolation_level)

        new_connection = no_pool_connection()
        new_connection.settings_dict["OPTIONS"][
            "isolation_level"
        ] = IsolationLevel.SERIALIZABLE
        try:
            # Start a transaction so the isolation level isn't reported as 0.
            new_connection.set_autocommit(False)
            # Check the level on the psycopg connection, not the Django
            # wrapper.
            self.assertEqual(
                new_connection.connection.isolation_level,
                IsolationLevel.SERIALIZABLE,
            )
        finally:
            new_connection.close()