def as_sql(self, compiler, connection):
        value_params = []
        lsql, params = compiler.compile(self.lhs)
        value_params.extend(params)

        rsql, params = compiler.compile(self.rhs)
        value_params.extend(params)

        combined_sql = f"({lsql} {self.connector} {rsql})"
        combined_value = combined_sql % tuple(value_params)
        return "%s", (combined_value,)