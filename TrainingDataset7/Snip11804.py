def as_sql(self, compiler, connection):
        # Avoid comparison against direct rhs if lhs is a boolean value. That
        # turns "boolfield__exact=True" into "WHERE boolean_field" instead of
        # "WHERE boolean_field = True" when allowed.
        if (
            isinstance(self.rhs, bool)
            and getattr(self.lhs, "conditional", False)
            and connection.ops.conditional_expression_supported_in_where_clause(
                self.lhs
            )
        ):
            lhs_sql, params = self.process_lhs(compiler, connection)
            template = "%s" if self.rhs else "NOT %s"
            return template % lhs_sql, params
        return super().as_sql(compiler, connection)