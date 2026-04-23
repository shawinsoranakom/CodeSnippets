def test_connect_invalid_isolation_level(self):
        self.assertIsNone(connection.connection.isolation_level)
        new_connection = no_pool_connection()
        new_connection.settings_dict["OPTIONS"]["isolation_level"] = -1
        msg = (
            "Invalid transaction isolation level -1 specified. Use one of the "
            "psycopg.IsolationLevel values."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            new_connection.ensure_connection()