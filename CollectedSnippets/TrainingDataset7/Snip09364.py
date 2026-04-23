def db_default_sql(self, field):
        """Return the sql and params for the field's database default."""
        from django.db.models.expressions import Value

        db_default = field._db_default_expression
        sql = (
            self._column_default_sql(field) if isinstance(db_default, Value) else "(%s)"
        )
        query = Query(model=field.model)
        compiler = query.get_compiler(connection=self.connection)
        default_sql, params = compiler.compile(db_default)
        if self.connection.features.requires_literal_defaults:
            # Some databases don't support parameterized defaults (Oracle,
            # SQLite). If this is the case, the individual schema backend
            # should implement prepare_default().
            default_sql %= tuple(self.prepare_default(p) for p in params)
            params = []
        return sql % default_sql, params