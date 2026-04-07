def _pk_constraint_sql(self, columns):
        return self.sql_pk_constraint % {
            "columns": ", ".join(self.quote_name(column) for column in columns)
        }