def test_pool_reuse(self):
        new_connection = no_pool_connection(alias="default_pool")
        new_connection.settings_dict["OPTIONS"]["pool"] = {
            "min": 0,
            "max": 2,
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
            get_connection()  # Get the second connection.
            sql = "select sys_context('userenv', 'sid') from dual"
            sids = [conn.cursor().execute(sql).fetchone()[0] for conn in connections]
            connection_1.close()  # Release back to the pool.
            connection_3 = get_connection()
            sid = connection_3.cursor().execute(sql).fetchone()[0]
            # Reuses the first connection as it is available.
            self.assertEqual(sid, sids[0])
        finally:
            # Release all connections back to the pool.
            for conn in connections:
                conn.close()
            new_connection.close_pool()