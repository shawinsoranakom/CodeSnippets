def __str__(self):
        sql, params = self.compiler.compile(self.expressions)
        params = map(self.quote_value, params)
        return sql % tuple(params)