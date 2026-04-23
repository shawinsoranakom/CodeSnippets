def as_sql(self, compiler, connection):
        # Skip the YearTransform above us (no possibility for efficient
        # lookup otherwise).
        real_lhs = self.lhs.lhs
        lhs_sql, params = self.process_lhs(compiler, connection, real_lhs)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        params = (*params, *rhs_params)
        # Build SQL where the integer year is concatenated with last month
        # and day, then convert that to date. (We try to have SQL like:
        #     WHERE somecol <= '2013-12-31')
        # but also make it work if the rhs_sql is field reference.
        return "%s <= (%s || '-12-31')::date" % (lhs_sql, rhs_sql), params