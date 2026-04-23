def test_bypass_role_configuration(self):
        from django.db.backends.postgresql.base import DatabaseWrapper

        class CustomDatabaseWrapper(DatabaseWrapper):
            def _configure_role(self, connection):
                return False

        new_connection = no_pool_connection()
        self.addCleanup(new_connection.close)
        new_connection.connect()

        settings = new_connection.settings_dict.copy()
        settings["OPTIONS"]["assume_role"] = "django_nonexistent_role"
        conn = new_connection.connection
        self.assertIs(
            CustomDatabaseWrapper(settings)._configure_connection(conn), False
        )