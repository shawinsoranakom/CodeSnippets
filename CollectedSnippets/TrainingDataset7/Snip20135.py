def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        # We need to be careful so that we get the params in right
        # places.
        params = lhs_params + rhs_params + lhs_params + rhs_params
        return (
            "%s >= date_trunc('month', %s) and "
            "%s < date_trunc('month', %s) + interval '1 months'" % (lhs, rhs, lhs, rhs),
            params,
        )