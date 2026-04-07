def process_rhs(self, compiler, connection):
        value = self.rhs
        if self.bilateral_transforms:
            if self.rhs_is_direct_value():
                # Do not call get_db_prep_lookup here as the value will be
                # transformed before being used for lookup
                value = Value(value, output_field=self.lhs.output_field)
            value = self.apply_bilateral_transforms(value)
            value = value.resolve_expression(compiler.query)
        if hasattr(value, "as_sql"):
            sql, params = compiler.compile(value)
            if isinstance(value, ColPairs):
                raise ValueError(
                    "CompositePrimaryKey cannot be used as a lookup value."
                )
            # Ensure expression is wrapped in parentheses to respect operator
            # precedence but avoid double wrapping as it can be misinterpreted
            # on some backends (e.g. subqueries on SQLite).
            if not isinstance(value, Value) and sql and sql[0] != "(":
                sql = "(%s)" % sql
            return sql, params
        else:
            return self.get_db_prep_lookup(value, connection)