def subtract_temporals(self, internal_type, lhs, rhs):
        if self.connection.features.supports_temporal_subtraction:
            lhs_sql, lhs_params = lhs
            rhs_sql, rhs_params = rhs
            return "(%s - %s)" % (lhs_sql, rhs_sql), (*lhs_params, *rhs_params)
        raise NotSupportedError(
            "This backend does not support %s subtraction." % internal_type
        )