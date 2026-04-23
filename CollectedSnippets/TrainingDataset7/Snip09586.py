def skip_default_on_alter(self, field):
        if self.skip_default(field):
            return True
        if self._is_limited_data_type(field) and not self.connection.mysql_is_mariadb:
            # MySQL doesn't support defaults for BLOB and TEXT in the
            # ALTER COLUMN statement.
            return True
        return False