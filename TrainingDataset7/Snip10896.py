def as_sql(self, compiler, connection):
        cols_sql = []
        cols_params = []
        cols = self.get_cols()

        for col in cols:
            sql, params = col.as_sql(compiler, connection)
            cols_sql.append(sql)
            cols_params.extend(params)

        return ", ".join(cols_sql), tuple(cols_params)