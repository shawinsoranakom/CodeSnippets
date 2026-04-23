def _field_db_check(self, field, field_db_params):
        if self.connection.mysql_is_mariadb:
            return super()._field_db_check(field, field_db_params)
        # On MySQL, check constraints with the column name as it requires
        # explicit recreation when the column is renamed.
        return field_db_params["check"]