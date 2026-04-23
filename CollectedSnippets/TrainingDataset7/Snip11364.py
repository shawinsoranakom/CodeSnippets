def as_oracle(self, compiler, connection):
        rhs, rhs_params = super().process_rhs(compiler, connection)
        if rhs_params and (*rhs_params,) == ("null",):
            # Field has key and it's NULL.
            has_key_expr = HasKeyOrArrayIndex(self.lhs.lhs, self.lhs.key_name)
            has_key_sql, has_key_params = has_key_expr.as_oracle(compiler, connection)
            is_null_expr = self.lhs.get_lookup("isnull")(self.lhs, True)
            is_null_sql, is_null_params = is_null_expr.as_sql(compiler, connection)
            return (
                "%s AND %s" % (has_key_sql, is_null_sql),
                tuple(has_key_params) + tuple(is_null_params),
            )
        return super().as_sql(compiler, connection)