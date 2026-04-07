def select_format(self, compiler, sql, params):
        # Wrap boolean expressions with a CASE WHEN expression if a database
        # backend (e.g. Oracle) doesn't support boolean expression in SELECT or
        # GROUP BY list.
        expression_supported_in_where_clause = (
            compiler.connection.ops.conditional_expression_supported_in_where_clause
        )
        if (
            not compiler.connection.features.supports_boolean_expr_in_select_clause
            # Avoid double wrapping.
            and expression_supported_in_where_clause(self.expression)
        ):
            sql = "CASE WHEN {} THEN 1 ELSE 0 END".format(sql)
        return sql, params