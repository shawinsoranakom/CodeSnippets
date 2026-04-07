def as_oracle(self, compiler, connection):
        sql, params = HasKeyOrArrayIndex(
            self.lhs.lhs,
            self.lhs.key_name,
        ).as_oracle(compiler, connection)
        if not self.rhs:
            return sql, params
        # Column doesn't have a key or IS NULL.
        lhs, lhs_params, _ = self.lhs.preprocess_lhs(compiler, connection)
        return "(NOT %s OR %s IS NULL)" % (sql, lhs), tuple(params) + tuple(lhs_params)