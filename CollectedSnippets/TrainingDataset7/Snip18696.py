def test_bypass_timezone_configuration(self):
        from django.db.backends.postgresql.base import DatabaseWrapper

        class CustomDatabaseWrapper(DatabaseWrapper):
            def _configure_timezone(self, connection):
                return False

        for Wrapper, commit in [
            (DatabaseWrapper, True),
            (CustomDatabaseWrapper, False),
        ]:
            with self.subTest(wrapper=Wrapper, commit=commit):
                new_connection = no_pool_connection()
                self.addCleanup(new_connection.close)

                # Set the database default time zone to be different from
                # the time zone in new_connection.settings_dict.
                with new_connection.cursor() as cursor:
                    cursor.execute("RESET TIMEZONE")
                    cursor.execute("SHOW TIMEZONE")
                    db_default_tz = cursor.fetchone()[0]
                new_tz = "Europe/Paris" if db_default_tz == "UTC" else "UTC"
                new_connection.timezone_name = new_tz

                settings = new_connection.settings_dict.copy()
                conn = new_connection.connection
                self.assertIs(Wrapper(settings)._configure_connection(conn), commit)