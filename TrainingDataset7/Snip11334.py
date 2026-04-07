def as_sql(self, compiler, connection, template=None):
        sql_parts = []
        params = []
        for lhs_sql, lhs_params, rhs_json_path in self._as_sql_parts(
            compiler, connection
        ):
            sql_parts.append(template % (lhs_sql, "%s"))
            params.extend([*lhs_params, rhs_json_path])
        return self._combine_sql_parts(sql_parts), tuple(params)