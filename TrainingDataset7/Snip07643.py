def _get_condition_sql(self, compiler, schema_editor, query):
        if self.condition is None:
            return None
        where = query.build_where(self.condition)
        sql, params = where.as_sql(compiler, schema_editor.connection)
        return sql % tuple(schema_editor.quote_value(p) for p in params)