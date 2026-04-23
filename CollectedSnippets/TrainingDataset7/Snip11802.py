def as_postgresql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = tuple(lhs_params) + tuple(rhs_params)
        return "%s %s %s" % (lhs, self.postgres_operator, rhs), params