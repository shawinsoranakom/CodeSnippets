def process_rhs(self, qn, connection):
        rhs, params = super().process_rhs(qn, connection)
        if params:
            params = (connection.ops.prep_for_iexact_query(params[0]), *params[1:])
        return rhs, params