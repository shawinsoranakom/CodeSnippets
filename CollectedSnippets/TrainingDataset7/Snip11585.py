def as_sql(self, compiler, connection):
        if isinstance(self.lhs, ColPairs):
            if self.rhs_is_direct_value():
                values = [get_normalized_value(value, self.lhs) for value in self.rhs]
                lookup = TupleIn(self.lhs, values)
            else:
                lookup = TupleIn(self.lhs, self.rhs)
            return compiler.compile(lookup)

        return super().as_sql(compiler, connection)