def process_lhs(self, compiler, connection):
        sql, params = super().process_lhs(compiler, connection)
        if isinstance(self.lhs, KeyTransform):
            return sql, params
        if connection.vendor == "mysql":
            return self._process_as_mysql(sql, params, connection)
        elif connection.vendor == "oracle":
            return self._process_as_oracle(sql, params, connection)
        elif connection.vendor == "sqlite":
            return self._process_as_sqlite(sql, params, connection)
        return sql, params