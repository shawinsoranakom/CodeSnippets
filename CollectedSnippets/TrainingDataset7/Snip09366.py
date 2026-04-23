def _column_generated_sql(self, field):
        """Return the SQL to use in a GENERATED ALWAYS clause."""
        expression_sql, params = field.generated_sql(self.connection)
        persistency_sql = self._column_generated_persistency_sql(field)
        if self.connection.features.requires_literal_defaults:
            expression_sql = expression_sql % tuple(self.quote_value(p) for p in params)
            params = ()
        return f"GENERATED ALWAYS AS ({expression_sql}) {persistency_sql}", params