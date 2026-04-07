def as_oracle(self, compiler, connection):
        # Use a custom delimiter to prevent the JSON path from escaping the SQL
        # literal. See comment in KeyTransform.
        template = "JSON_EXISTS(%s, q'\uffff%s\uffff')"
        sql_parts = []
        params = []
        for lhs_sql, lhs_params, rhs_json_path in self._as_sql_parts(
            compiler, connection
        ):
            # Add right-hand-side directly into SQL because it cannot be passed
            # as bind variables to JSON_EXISTS. It might result in invalid
            # queries but it is assumed that it cannot be evaded because the
            # path is JSON serialized.
            sql_parts.append(template % (lhs_sql, rhs_json_path))
            params.extend(lhs_params)
        return self._combine_sql_parts(sql_parts), tuple(params)