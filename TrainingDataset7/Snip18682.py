def test_connect_custom_cursor_factory(self):
        """
        A custom cursor factory can be configured with DATABASES["options"]
        ["cursor_factory"].
        """
        from django.db.backends.postgresql.base import Cursor

        class MyCursor(Cursor):
            pass

        new_connection = no_pool_connection()
        new_connection.settings_dict["OPTIONS"]["cursor_factory"] = MyCursor
        try:
            new_connection.connect()
            self.assertEqual(new_connection.connection.cursor_factory, MyCursor)
        finally:
            new_connection.close()