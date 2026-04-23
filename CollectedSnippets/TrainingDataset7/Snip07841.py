def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = (*lhs_params, *rhs_params)
        return "%s @@ %s" % (lhs, rhs), params