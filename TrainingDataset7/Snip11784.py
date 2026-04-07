def as_oracle(self, compiler, connection):
        # Oracle doesn't allow EXISTS() and filters to be compared to another
        # expression unless they're wrapped in a CASE WHEN.
        wrapped = False
        exprs = []
        for expr in (self.lhs, self.rhs):
            if connection.ops.conditional_expression_supported_in_where_clause(expr):
                expr = Case(When(expr, then=True), default=False)
                wrapped = True
            exprs.append(expr)
        lookup = type(self)(*exprs) if wrapped else self
        return lookup.as_sql(compiler, connection)