def as_sql(self, compiler, connection):
        lhs_sql, lhs_params = self.process_lhs(compiler, connection)
        rhs_sql, rhs_params = self.process_rhs(compiler, connection)
        sql_params = (*lhs_params, *rhs_params)

        template_params = {
            "lhs": lhs_sql,
            "rhs": rhs_sql,
            "value": "%s",
            **self.template_params,
        }
        rhs_op = self.get_rhs_op(connection, rhs_sql)
        return rhs_op.as_sql(connection, self, template_params, sql_params)