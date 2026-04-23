def has_table(self):
        """Return True if the django_migrations table exists."""
        # If the migrations table has already been confirmed to exist, don't
        # recheck it's existence.
        if self._has_table:
            return True
        # It hasn't been confirmed to exist, recheck.
        with self.connection.cursor() as cursor:
            tables = self.connection.introspection.table_names(cursor)

        self._has_table = self.Migration._meta.db_table in tables
        return self._has_table