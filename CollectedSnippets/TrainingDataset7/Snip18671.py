def test_connect_pool(self):
        from psycopg_pool import PoolTimeout

        new_connection = no_pool_connection(alias="default_pool")
        new_connection.settings_dict["OPTIONS"]["pool"] = {
            "min_size": 0,
            "max_size": 2,
            "timeout": 5,
        }
        self.assertIsNotNone(new_connection.pool)

        connections = []

        def get_connection():
            # copy() reuses the existing alias and as such the same pool.
            conn = new_connection.copy()
            conn.connect()
            connections.append(conn)
            return conn

        try:
            connection_1 = get_connection()  # First connection.
            connection_1_backend_pid = connection_1.connection.info.backend_pid
            get_connection()  # Get the second connection.
            with self.assertRaises(PoolTimeout):
                # The pool has a maximum of 2 connections.
                get_connection()

            connection_1.close()  # Release back to the pool.
            connection_3 = get_connection()
            # Reuses the first connection as it is available.
            self.assertEqual(
                connection_3.connection.info.backend_pid, connection_1_backend_pid
            )
        finally:
            # Release all connections back to the pool.
            for conn in connections:
                conn.close()
            new_connection.close_pool()