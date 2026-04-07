def _column_default_sql(self, field):
        if not self.connection.mysql_is_mariadb and self._is_limited_data_type(field):
            # MySQL supports defaults for BLOB and TEXT columns only if the
            # default value is written as an expression i.e. in parentheses.
            return "(%s)"
        return super()._column_default_sql(field)