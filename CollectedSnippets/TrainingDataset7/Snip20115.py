def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = (*lhs_params, *rhs_params)
        return "(%s) %%%% 3 = %s" % (lhs, rhs), params