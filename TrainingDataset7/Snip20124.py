def as_sql(self, compiler, connection):
        # We will need to skip the extract part, and instead go
        # directly with the originating field, that is self.lhs.lhs
        lhs_sql, lhs_params = self.process_lhs(compiler, connection, self.lhs.lhs)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        # Note that we must be careful so that we have params in the
        # same order as we have the parts in the SQL.
        params = lhs_params + rhs_params + lhs_params + rhs_params
        # We use PostgreSQL specific SQL here. Note that we must do the
        # conversions in SQL instead of in Python to support F() references.
        return (
            "%(lhs)s >= (%(rhs)s || '-01-01')::date "
            "AND %(lhs)s <= (%(rhs)s || '-12-31')::date"
            % {"lhs": lhs_sql, "rhs": rhs_sql},
            params,
        )