def test_connect_server_side_binding(self):
        """
        The server-side parameters binding role can be enabled with DATABASES
        ["OPTIONS"]["server_side_binding"].
        """
        from django.db.backends.postgresql.base import ServerBindingCursor

        new_connection = no_pool_connection()
        new_connection.settings_dict["OPTIONS"]["server_side_binding"] = True
        try:
            new_connection.connect()
            self.assertEqual(
                new_connection.connection.cursor_factory,
                ServerBindingCursor,
            )
        finally:
            new_connection.close()