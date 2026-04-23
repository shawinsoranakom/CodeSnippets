def _create_check_sql(self, model, name, check):
        if not self.connection.features.supports_table_check_constraints:
            return None
        return Statement(
            self.sql_create_check,
            table=Table(model._meta.db_table, self.quote_name),
            name=self.quote_name(name),
            check=check,
        )