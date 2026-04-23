def process_rhs(self, compiler, connection):
        if isinstance(self.rhs, Query):
            # If rhs is some Query, don't touch it.
            return super().process_rhs(compiler, connection)
        if isinstance(self.rhs, Expression):
            rhs = self.rhs.resolve_expression(compiler.query)
        else:
            rhs = connection.ops.Adapter(self.rhs)
        return connection.ops.get_geom_placeholder_sql(
            self.lhs.output_field, rhs, compiler
        )