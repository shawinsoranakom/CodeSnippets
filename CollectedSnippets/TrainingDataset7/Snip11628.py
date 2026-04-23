def as_sqlite(self, compiler, connection):
        if connection.get_database_version() < (3, 37) and isinstance(
            first_expr := self.source_expressions[0], Tuple
        ):
            first_expr = first_expr.copy()
            first_expr.function = "VALUES"
            return Tuple(first_expr, *self.source_expressions[1:]).as_sql(
                compiler, connection
            )
        return self.as_sql(compiler, connection)