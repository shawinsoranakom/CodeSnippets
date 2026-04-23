def as_custom_sql(self, compiler, connection):
                lhs_sql, lhs_params = self.process_lhs(
                    compiler, connection, self.lhs.lhs
                )
                rhs_sql, rhs_params = self.process_rhs(compiler, connection)
                params = lhs_params + rhs_params + lhs_params + rhs_params
                return (
                    "%(lhs)s >= "
                    "str_to_date(concat(%(rhs)s, '-01-01'), '%%%%Y-%%%%m-%%%%d') "
                    "AND %(lhs)s <= "
                    "str_to_date(concat(%(rhs)s, '-12-31'), '%%%%Y-%%%%m-%%%%d')"
                    % {"lhs": lhs_sql, "rhs": rhs_sql},
                    params,
                )