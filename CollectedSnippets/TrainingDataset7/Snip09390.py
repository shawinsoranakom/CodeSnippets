def _alter_column_database_default_sql(
        self, model, old_field, new_field, drop=False
    ):
        """
        Hook to specialize column database default alteration.

        Return a (sql, params) fragment to add or drop (depending on the drop
        argument) a default to new_field's column.
        """
        if drop:
            sql = self.sql_alter_column_no_default
            default_sql = ""
            params = []
        else:
            sql = self.sql_alter_column_default
            default_sql, params = self.db_default_sql(new_field)

        new_db_params = new_field.db_parameters(connection=self.connection)
        return (
            sql
            % {
                "column": self.quote_name(new_field.column),
                "type": new_db_params["type"],
                "default": default_sql,
            },
            params,
        )