def as_sql(self, compiler, connection):
        lhs_sql, params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        params = (*params, *rhs_params)
        rhs_sql = self.get_rhs_op(connection, rhs_sql)
        return "%s %s" % (lhs_sql, rhs_sql), params