def as_oracle(self, compiler, connection):
        if (
            connection.features.supports_primitives_in_json_field
            and isinstance(self.rhs, expressions.ExpressionList)
            and expressions.JSONNull() in self.rhs.get_source_expressions()
        ):
            # Break the lookup into multiple exact lookups combined with OR, as
            # Oracle does not support directly extracting JSON scalar null as a
            # value in the right-hand side of an IN clause.
            exact_lookup = self.lhs.get_lookup("exact")
            sql_parts = []
            all_params = ()
            for expr in self.rhs.get_source_expressions():
                lookup = exact_lookup(self.lhs, expr)
                sql, params = lookup.as_oracle(compiler, connection)
                sql_parts.append(f"({sql})")
                all_params = (*all_params, *params)
            sql = " OR ".join(sql_parts)
            return sql, all_params
        return self.as_sql(compiler, connection)